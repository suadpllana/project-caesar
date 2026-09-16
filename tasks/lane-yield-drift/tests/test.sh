#!/bin/bash
# The verifier's entry point. The order is the point of it.
#
# The reward channel is locked and defaulted to 0 before anything the agent
# wrote can run. The answers - gt.json, the grader and the sealed model - are
# made root-only. A fresh tree is assembled from the pristine copy with only
# the four declared paths laid over it, owned by root and read-only to the run.
# The run then happens as an unprivileged uid, in its own session, under a hard
# wall clock, reporting into a descriptor root opened and handed down, so the
# uid that executes agent code owns nothing it is graded on. Survivors are
# reaped, both exit statuses are checked, and only then does the grader run, as
# root, importing nothing the agent wrote.
set -Eeuo pipefail

install -d -m 700 -o root -g root /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown -R root:root /tests/gt.json /tests/test_outputs.py /tests/seal
chmod 600 /tests/gt.json /tests/test_outputs.py
chmod 700 /tests/seal
chmod 600 /tests/seal/model.py

rm -rf /work
mkdir -p /work/app /work/run
cp -a /pristine/. /work/app/
for f in sked/zt.py sked/due.py sked/gate.py sked/lane.py; do
  [ -f "/app/$f" ] && cp -f "/app/$f" "/work/app/$f"
done
find /work/app \( -name __pycache__ -o -name '*.pyc' \) -exec rm -rf {} + 2>/dev/null || true
chown -R root:root /work
chmod -R u=rwX,go=rX /work/app
chmod 755 /work /work/run
install -d -m 700 -o lane -g lane /work/scratch

: > /work/run/out.json
chmod 600 /work/run/out.json

RUN_NONCE="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
RUN_COUNT="${RUN_COUNT:-50}"
export RUN_NONCE RUN_COUNT

set +e
exec 9>/work/run/out.json
setsid --wait env APPDIR=/work/app HOME=/work/scratch TMPDIR=/work/scratch \
    PYTHONDONTWRITEBYTECODE=1 RUN_NONCE="$RUN_NONCE" RUN_COUNT="$RUN_COUNT" \
  setpriv --reuid=1004 --regid=1004 --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py fd:9
run_status=$?
exec 9>&-
python /tests/reap.py 1004
reap_status=$?
set -e
[ "$run_status" -eq 0 ] && [ "$reap_status" -eq 0 ] || exit 1

if RUN_OUT=/work/run/out.json APP_DIR=/work/app PRISTINE_DIR=/pristine REQUIRE_MONITORING=1 \
   pytest -rA --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
