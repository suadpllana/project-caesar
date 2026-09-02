#!/bin/bash
# Verifier entry point.
#
# One rule shapes every line of this: the reward, and everything the reward is
# derived from, must live where executed agent code cannot write.
#
# So the reward channel is locked and defaulted to 0 before a line of the agent's
# work is loaded. The tree the run executes is assembled root-owned and read-only
# from an untouched copy with only the four declared artifacts laid over it, which
# makes an edit anywhere else impossible rather than merely detectable. The file
# the run publishes into is opened here, by root, and handed across as an
# inherited descriptor after privilege is dropped, so the uid executing agent code
# does not own the file it is graded on. The run gets its own session and a wall
# clock timeout, and survivors are reaped before anything is read. Grading happens
# afterwards as root, under pytest, which executes nothing the agent wrote and
# reads the model and the answers out of files the run could not open.
#
# The nonce is drawn here, once the agent has stopped, and seeds the three hundred
# plans the submission is really graded on. Both sides are handed the same nonce so
# the run and the grader are talking about the same plans.
set -Eeuo pipefail

mkdir -p /logs/verifier
chown root:root /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown root:root /tests/gt.json /tests/oracle.py /tests/test_outputs.py
chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py

rm -rf /work
mkdir -p /work/app /work/run
cp -a /pristine/. /work/app/

# Only the declared artifacts are laid over. One the agent never wrote is simply
# absent, and the shipped file stands.
for rel in flow/emit.py flow/route.py flow/due.py flow/pick.py; do
  if [ -f "/app/$rel" ]; then
    cp -f "/app/$rel" "/work/app/$rel"
  fi
done
find /work/app -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find /work/app -name '*.pyc' -delete 2>/dev/null || true

chown -R root:root /work
chmod -R u=rwX,go=rX /work/app
chmod 755 /work /work/run
install -d -o sandbox -g sandbox -m 700 /work/scratch

: > /work/run/out.json
chown root:root /work/run/out.json
chmod 600 /work/run/out.json

RUN_NONCE="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
RUN_COUNT=300
export RUN_NONCE RUN_COUNT

set +e
exec 8>/work/run/out.json
setsid --wait env APPDIR=/work/app TMPDIR=/work/scratch HOME=/work/scratch \
    PYTHONDONTWRITEBYTECODE=1 RUN_NONCE="$RUN_NONCE" RUN_COUNT="$RUN_COUNT" \
  setpriv --reuid=1002 --regid=1002 --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py fd:8
exec 8>&-
python /tests/reap.py 1002
set -e

if RUN_OUT=/work/run/out.json APP_DIR=/work/app PRISTINE_DIR=/pristine \
   pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
