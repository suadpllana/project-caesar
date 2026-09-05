#!/bin/bash
# The verifier's entry point. The order is the point of it.
#
# First the reward channel is locked down and defaulted to 0, and the three files a run
# must never read (the ground truth, the sealed model, the grader) are made root-only.
# Then a fresh work tree is assembled from the pristine copy with only the four declared
# artifacts laid over it, owned by root and read-only to the run. Then the run happens as
# an unprivileged uid, in its own session, under a hard timeout, reporting into a file
# that root opened and handed down as a descriptor, so the uid executing agent code owns
# nothing it is graded on. Then survivors are reaped, and only then does pytest run, as
# root, never importing anything the agent wrote.
#
# The nonce is drawn here, after the agent has finished. It seeds the generated scripts
# on both sides, so the run and the grader are talking about the same three hundred.
set -Eeuo pipefail

install -d -m 700 -o root -g root /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown root:root /tests/gt.json /tests/oracle.py /tests/test_outputs.py
chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py

rm -rf /work
mkdir -p /work/app /work/run
cp -a /pristine/. /work/app/
for f in ui/focus.py ui/keep.py ui/reach.py ui/mem.py; do
  [ -f "/app/$f" ] && cp -f "/app/$f" "/work/app/$f"
done
find /work/app \( -name __pycache__ -o -name '*.pyc' \) -exec rm -rf {} + 2>/dev/null || true
chown -R root:root /work
chmod -R u=rwX,go=rX /work/app
chmod 755 /work /work/run
install -d -m 700 -o trail -g trail /work/scratch

: > /work/run/out.json
chmod 600 /work/run/out.json

RUN_NONCE="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
RUN_COUNT="${RUN_COUNT:-300}"
export RUN_NONCE RUN_COUNT

set +e
exec 9>/work/run/out.json
setsid --wait env APPDIR=/work/app HOME=/work/scratch TMPDIR=/work/scratch \
    PYTHONDONTWRITEBYTECODE=1 RUN_NONCE="$RUN_NONCE" RUN_COUNT="$RUN_COUNT" \
  setpriv --reuid=1003 --regid=1003 --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py fd:9
exec 9>&-
python /tests/reap.py 1003
set -e

if RUN_OUT=/work/run/out.json APP_DIR=/work/app PRISTINE_DIR=/pristine REQUIRE_MONITORING=1 \
   pytest -rA --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
