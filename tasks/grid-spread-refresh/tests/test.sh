#!/bin/bash
# The verifier's entry point, in the order that makes it safe.
#
# The reward channel is locked and defaulted to 0 before anything the submission wrote can
# run, and the three files a run must never read - the hand derivations, the sealed model
# and the grader - are made root-only. A work tree is then assembled from the pristine copy
# with only the four declared policy files laid over it, owned by root and read-only to the
# run. The run happens as an unprivileged uid, in its own session, under a hard wall clock,
# writing into a descriptor root opened before the privilege drop, so the uid that executes
# submitted code owns nothing the verdict is read from. Survivors are killed. Only then does
# pytest run, as root, importing nothing the submission wrote.
#
# The nonce attests this run; the script families come from fixed versioned seeds.
set -Eeuo pipefail

install -d -m 700 -o root -g root /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown root:root /tests/gt.json /tests/oracle.py /tests/test_outputs.py
chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py

rm -rf /work
mkdir -p /work/app /work/run
cp -a /pristine/. /work/app/
for f in sheet/dep.py sheet/lay.py sheet/upd.py sheet/flow.py; do
  [ -f "/app/$f" ] && cp -f "/app/$f" "/work/app/$f"
done
find /work/app \( -name __pycache__ -o -name '*.pyc' \) -exec rm -rf {} + 2>/dev/null || true
chown -R root:root /work
chmod -R u=rwX,go=rX /work/app
chmod 755 /work /work/run
install -d -m 700 -o rerun -g rerun /work/scratch

: > /work/run/out.json
chmod 600 /work/run/out.json

RUN_NONCE="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
RUN_COUNT="${RUN_COUNT:-60}"
export RUN_NONCE RUN_COUNT

set +e
exec 9>/work/run/out.json
setsid --wait env APPDIR=/work/app HOME=/work/scratch TMPDIR=/work/scratch \
    PYTHONDONTWRITEBYTECODE=1 RUN_NONCE="$RUN_NONCE" RUN_COUNT="$RUN_COUNT" \
  setpriv --reuid=1004 --regid=1004 --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py fd:9
run_status=$?
exec 9>&-
python /tests/sweepup.py 1004
reap_status=$?
set -e
[ "$run_status" -eq 0 ] && [ "$reap_status" -eq 0 ] || exit 1

if RUN_OUT=/work/run/out.json APP_DIR=/work/app PRISTINE_DIR=/pristine REQUIRE_MONITORING=1 \
   pytest -rA --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
