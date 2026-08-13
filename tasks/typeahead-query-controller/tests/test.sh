#!/usr/bin/env bash
# Verifier entry point.
#
# Contract: /logs/verifier/reward.txt always ends up containing exactly "0" or
# "1", on every path including crashes, and a CTRF report is emitted whenever
# pytest manages to run.

set -uo pipefail

REWARD_DIR="/logs/verifier"
REWARD_FILE="${REWARD_DIR}/reward.txt"
mkdir -p "${REWARD_DIR}"

# Fail closed: any unexpected exit leaves a 0 behind.
printf '0' > "${REWARD_FILE}"

# ---------------------------------------------------------------------------
# Lock the reward channel down before anything derived from the agent's tree
# is executed.
#
# Vite evaluates vite.config.ts as code. That config is pinned from this image
# (see below), but plugins, postcss configs and transitively imported modules
# inside the agent's tree can still reach the module graph, so the dev server
# is treated as untrusted and runs as an unprivileged user. root owns the
# reward directory 0700 so nothing that server executes can read, write or
# replace reward.txt.
# ---------------------------------------------------------------------------
chown -R root:root "${REWARD_DIR}" 2>/dev/null || true
chmod 700 "${REWARD_DIR}" 2>/dev/null || true
chmod 600 "${REWARD_FILE}" 2>/dev/null || true

APP_DIR="${APP_DIR:-/app}"
export APP_DIR

log() { printf '[verifier] %s\n' "$*" >&2; }

finish() {
  local code="$1"
  printf '%s' "${code}" > "${REWARD_FILE}"
  log "reward=${code}"
  exit 0
}

if [ ! -d "${APP_DIR}/src" ]; then
  log "no ${APP_DIR}/src -- nothing to verify"
  finish 0
fi

# ---------------------------------------------------------------------------
# Serve the agent's app.
#
# A copy is used so the served tree is pristine w.r.t. node_modules while the
# agent's source is exactly what it wrote. Vite is taken from the image.
# ---------------------------------------------------------------------------
WORK="$(mktemp -d /tmp/verify.XXXXXX)"
mkdir -p "${WORK}/app"

# Only the agent's SOURCE is taken. Everything that Vite executes as part of
# starting up -- the config, the tsconfig, package.json (which can carry a
# "type" field and postcss/browserslist hooks) -- comes from this image, not
# from the agent, so the dev server cannot be turned into an execution vector.
cp -r "${APP_DIR}/src" "${WORK}/app/src" 2>/dev/null || true
cp -r "${APP_DIR}/public" "${WORK}/app/public" 2>/dev/null || true
cp /tests/pristine/tsconfig.json   "${WORK}/app/" 2>/dev/null || true
cp /tests/pristine/vite.config.ts  "${WORK}/app/" 2>/dev/null || true
cp /tests/pristine/package.json    "${WORK}/app/" 2>/dev/null || true

# Anything the agent may have dropped into src/ that Vite would auto-load as
# configuration rather than as a module under test.
find "${WORK}/app/src" -maxdepth 1 -type f \
     \( -name 'vite.config.*' -o -name 'postcss.config.*' \
        -o -name 'tailwind.config.*' -o -name '.babelrc*' \
        -o -name 'babel.config.*' \) -delete 2>/dev/null || true

# node_modules from the verifier image, so the agent cannot swap the bundler.
ln -s /verifier/node_modules "${WORK}/app/node_modules" 2>/dev/null || true

export APP_DIR="${WORK}/app"

# The dev server evaluates code derived from the agent's tree, so it runs as
# an unprivileged user that cannot touch /logs/verifier.
chown -R verifier:verifier "${WORK}" 2>/dev/null || true

log "starting vite on 127.0.0.1:5173 as unprivileged user"
(
  cd "${WORK}/app" \
    && setpriv --reuid=verifier --regid=verifier --init-groups --inh-caps=-all \
         /verifier/node_modules/.bin/vite \
         --host 127.0.0.1 --port 5173 --strictPort \
       >"${WORK}/vite.log" 2>&1
) &
VITE_PID=$!

cleanup() {
  kill "${VITE_PID}" 2>/dev/null || true
  wait "${VITE_PID}" 2>/dev/null || true
}
trap cleanup EXIT

# Wait for the dev server (bounded).
READY=0
for _ in $(seq 1 90); do
  if curl -fsS -o /dev/null "http://127.0.0.1:5173/"; then
    READY=1
    break
  fi
  sleep 1
done

if [ "${READY}" -ne 1 ]; then
  log "vite never became ready"
  log "--- vite.log ---"
  tail -50 "${WORK}/vite.log" >&2 || true
  finish 0
fi

# ---------------------------------------------------------------------------
# Drive the browser.
# ---------------------------------------------------------------------------
log "running conformance driver"
if ! node /tests/run_conformance.js > /tmp/conformance.json 2>/tmp/driver.err; then
  log "driver exited non-zero"
  tail -30 /tmp/driver.err >&2 || true
fi

if [ ! -s /tmp/conformance.json ]; then
  log "driver produced no report"
  tail -30 /tmp/driver.err >&2 || true
  printf '{}' > /tmp/conformance.json
fi

# ---------------------------------------------------------------------------
# Grade.
#
# Everything derived from the agent's tree is torn down first: no untrusted
# process may still be running while the reward is decided, so nothing can
# race or re-write the verdict after it is written.
# ---------------------------------------------------------------------------
log "stopping untrusted processes before grading"
kill "${VITE_PID}" 2>/dev/null || true
wait "${VITE_PID}" 2>/dev/null || true
pkill -u verifier 2>/dev/null || true
sleep 1
if pgrep -u verifier >/dev/null 2>&1; then
  pkill -9 -u verifier 2>/dev/null || true
  sleep 1
fi
if pgrep -u verifier >/dev/null 2>&1; then
  log "unprivileged processes survived teardown -- refusing to grade"
  finish 0
fi

# Re-assert ownership of the reward channel in case anything touched it.
chown -R root:root "${REWARD_DIR}" 2>/dev/null || true
chmod 700 "${REWARD_DIR}" 2>/dev/null || true
printf '0' > "${REWARD_FILE}"
chmod 600 "${REWARD_FILE}" 2>/dev/null || true

cd /tests

python -m pytest test_conformance.py \
  -p no:cacheprovider \
  -q \
  --ctrf /logs/verifier/ctrf.json
PYTEST_RC=$?

if [ "${PYTEST_RC}" -eq 0 ]; then
  finish 1
fi

finish 0
