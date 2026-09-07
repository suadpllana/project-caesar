#!/bin/bash
# What this script is arranged to guarantee, in the order it guarantees it.
#
#   1  the reward is root's, in a directory nothing else may enter, and it says 0
#   2  the answers, the model and the grader are readable by root and by nobody else
#   3  the tree that will execute is built from the untouched copy, with only the four
#      declared files laid over it, and it is read-only to whoever executes it
#   4  the report is a file root opened; the executing uid is handed the descriptor and
#      never the path, so it owns nothing the verdict is read from
#   5  the run happens in a session of its own, unprivileged, under a hard clock
#   6  nothing of that run is still alive when grading starts
#   7  the grader runs as root, imports nothing the submission wrote, and is the only
#      thing that ever writes 1
#
# Each step's status is checked. A stage that did not finish is a failed run, never a
# pass by default.
set -Eeuo pipefail

SANDBOX_UID=1004
REPORT=/work/run/out.json
export RUN_COUNT="${RUN_COUNT:-120}"
export RUN_NONCE="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"

# 1 and 2
install -d -m 700 -o root -g root /logs/verifier
echo 0 > /logs/verifier/reward.txt
for sealed in gt.json oracle.py test_outputs.py; do
  chown root:root "/tests/${sealed}"
  chmod 600 "/tests/${sealed}"
done

# 3
rm -rf /work
install -d -m 755 /work /work/run
cp -a /pristine /work/app
for laid in sheet/val.py sheet/see.py sheet/lay.py sheet/memo.py; do
  if [ -f "/app/${laid}" ]; then cp -f "/app/${laid}" "/work/app/${laid}"; fi
done
find /work/app \( -name __pycache__ -o -name '*.pyc' \) -prune -exec rm -rf {} + || true
chown -R root:root /work
chmod -R u=rwX,go=rX /work/app
install -d -m 700 -o "${SANDBOX_UID}" -g "${SANDBOX_UID}" /work/scratch

# 4
: > "${REPORT}"
chmod 600 "${REPORT}"
exec 8>"${REPORT}"

# 5
set +e
setsid --wait \
  env APPDIR=/work/app HOME=/work/scratch TMPDIR=/work/scratch \
      PYTHONDONTWRITEBYTECODE=1 RUN_NONCE="${RUN_NONCE}" RUN_COUNT="${RUN_COUNT}" \
  setpriv --reuid="${SANDBOX_UID}" --regid="${SANDBOX_UID}" --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py fd:8
worker=$?
set -e
exec 8>&-

# 6
set +e
python /tests/reap.py "${SANDBOX_UID}"
swept=$?
set -e

if [ "${worker}" -ne 0 ] || [ "${swept}" -ne 0 ]; then
  echo "run did not finish cleanly (worker ${worker}, sweep ${swept})" >&2
  exit 1
fi

# 7
if RUN_OUT="${REPORT}" APP_DIR=/work/app PRISTINE_DIR=/pristine REQUIRE_MONITORING=1 \
   pytest -rA --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
