#!/usr/bin/env bash
# Verifier entry point.
#
# /logs/verifier/reward.txt always ends up holding exactly "0" or "1", down
# every path including a crash. A CTRF report is written whenever pytest gets
# far enough to produce one.
#
# The separation that matters here is that the part does not exist in the
# process holding the agent's code. The apply path is compiled into a small
# binary that runs as an unprivileged user and asks for bus transactions on a
# pipe; the register file, the fault rules, the sessions and the transaction
# count all live in Python inside a root-only /tests.

set -uo pipefail

REWARD_DIR="/logs/verifier"
REWARD_FILE="${REWARD_DIR}/reward.txt"
VERDICT_FILE="${REWARD_DIR}/verdict.json"
mkdir -p "${REWARD_DIR}"

printf '0' > "${REWARD_FILE}"

chown -R root:root "${REWARD_DIR}" 2>/dev/null || true
chmod 700 "${REWARD_DIR}" 2>/dev/null || true
chmod 600 "${REWARD_FILE}" 2>/dev/null || true
rm -f "${VERDICT_FILE}" 2>/dev/null || true

APP_DIR="${APP_DIR:-/app}"

say() { printf '[verifier] %s\n' "$*" >&2; }

finish() {
  printf '%s' "$1" > "${REWARD_FILE}"
  say "reward=$1"
  exit 0
}

if [ ! -f "${APP_DIR}/src/driver.c" ]; then
  say "there is no ${APP_DIR}/src/driver.c to grade"
  finish 0
fi

# ---------------------------------------------------------------------------
# Build the runner. driver.c is the only thing taken from the agent; the
# header and the runner itself come out of this image, so a redefined register
# map cannot change what a session means.
#
# The compiler runs as the unprivileged account, not as root, so a driver that
# tries to #include its way into /tests gets nothing.
# ---------------------------------------------------------------------------
WORK="$(mktemp -d /tmp/verify.XXXXXX)"
chmod 755 "${WORK}"
cp "${APP_DIR}/src/driver.c" "${WORK}/driver.c"
chmod 644 "${WORK}/driver.c"

# The compiler runs as verifier, so it needs somewhere it can actually write:
# the link step creates the binary, and a root-owned directory refuses it.
BUILD="${WORK}/build"
mkdir -p "${BUILD}"
chown verifier:verifier "${BUILD}" 2>/dev/null || chmod 777 "${BUILD}"

if ! setpriv --reuid verifier --regid verifier --init-groups --inh-caps -all -- \
      cc -std=c11 -O2 -o "${BUILD}/runner" \
         /probe/runner.c "${WORK}/driver.c" \
         -I /probe/include >"${WORK}/build.log" 2>&1; then
  say "the apply path did not build"
  tail -20 "${WORK}/build.log" >&2 || true
  finish 0
fi
if [ ! -x "${BUILD}/runner" ]; then
  say "the build reported success and produced nothing"
  finish 0
fi
chmod 755 "${BUILD}/runner"

# ---------------------------------------------------------------------------
# Grade. pytest runs as root out of /tests, and /tests is root-only, so the
# account the runner uses cannot read the part model, the sessions or the
# ceiling. The seed is drawn fresh, so a verdict kept from an earlier run is
# worth nothing.
# ---------------------------------------------------------------------------
CHECK_NONCE="$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')"
CHECK_SEED="$(head -c 4 /dev/urandom | od -An -tu4 | tr -d ' \n')"
export CHECK_NONCE CHECK_SEED
export CHECK_RUNNER="${BUILD}/runner"
export CHECK_APP="${APP_DIR}"
export CHECK_PRISTINE="/tests/pristine"
export CHECK_USER="verifier"
export CHECK_VERDICT="${VERDICT_FILE}"

say "running the sessions (seed ${CHECK_SEED})"
cd /tests

python -m pytest test_driver.py \
  -p no:cacheprovider \
  -q \
  --ctrf "${REWARD_DIR}/ctrf.json" \
  >"${WORK}/pytest.log" 2>&1
PYTEST_RC=$?

tail -40 "${WORK}/pytest.log" >&2 || true

# ---------------------------------------------------------------------------
# Nothing built out of the agent's file may still be alive when the reward is
# decided.
# ---------------------------------------------------------------------------
pkill -u verifier 2>/dev/null || true
sleep 2
if pgrep -u verifier >/dev/null 2>&1; then
  pkill -9 -u verifier 2>/dev/null || true
  sleep 3
fi
if pgrep -u verifier >/dev/null 2>&1; then
  say "unprivileged processes outlived the run -- refusing to grade"
  finish 0
fi

chown -R root:root "${REWARD_DIR}" 2>/dev/null || true
chmod 700 "${REWARD_DIR}" 2>/dev/null || true
printf '0' > "${REWARD_FILE}"
chmod 600 "${REWARD_FILE}" 2>/dev/null || true

if [ "${PYTEST_RC}" -ne 0 ]; then
  say "pytest exited ${PYTEST_RC}"
  finish 0
fi

if [ ! -s "${VERDICT_FILE}" ]; then
  say "no verdict was written -- an exit code on its own decides nothing"
  finish 0
fi

# The other grading path: plain Python, pytest nowhere near it, its own build
# and its own seed.
say "second opinion"
if ! python /tests/crosscheck.py >&2; then
  say "the second opinion disagreed"
  finish 0
fi

if ! python - "${VERDICT_FILE}" "${CHECK_NONCE}" <<'PY'
import json, sys
try:
    verdict = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception as exc:
    print(f"[verifier] the verdict will not parse: {exc}", file=sys.stderr)
    raise SystemExit(1)
if verdict.get("nonce") != sys.argv[2]:
    print("[verifier] that verdict belongs to a different run", file=sys.stderr)
    raise SystemExit(1)
if verdict.get("exitstatus") != 0 or not verdict.get("passed"):
    print("[verifier] the verdict is not a pass", file=sys.stderr)
    raise SystemExit(1)
PY
then
  finish 0
fi

finish 1
