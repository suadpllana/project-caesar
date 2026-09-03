#!/bin/bash
# Verifier entry point.
#
# Everything the reward is derived from has to live where executed agent code
# cannot write, so the order below is the argument rather than a convenience.
#
# The reward channel is locked and defaulted to 0 before any of the agent's work
# is loaded. The tree the run executes is built root-owned and read-only from an
# untouched copy, with only the four declared artifacts laid over it, which makes
# an edit anywhere else impossible rather than merely detectable. The file the run
# publishes into is opened here, by root, and handed over as an inherited
# descriptor after the privilege drop, so the uid running agent code does not own
# the file it is graded on. The run gets its own session and a wall clock; what it
# leaves behind is reaped before anything is read. Grading then happens as root
# under pytest, which executes nothing the agent wrote.
#
# The nonce is drawn here, once the agent has stopped, and seeds the sets the
# submission is really graded on. The run and the grader are handed the same one
# so they are talking about the same sets.
set -Eeuo pipefail

mkdir -p /logs/verifier
chown root:root /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown root:root /tests/gt.json /tests/oracle.py /tests/test_outputs.py
chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py

rm -rf /box
mkdir -p /box/app /box/say
cp -a /pristine/. /box/app/

for rel in bind/rch.py bind/hold.py bind/card.py bind/seq.py; do
  if [ -f "/app/$rel" ]; then
    cp -f "/app/$rel" "/box/app/$rel"
  fi
done
find /box/app -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find /box/app -name '*.pyc' -delete 2>/dev/null || true

chown -R root:root /box
chmod -R u=rwX,go=rX /box/app
chmod 755 /box /box/say
install -d -o sandbox -g sandbox -m 700 /box/tmp

: > /box/say/out.json
chown root:root /box/say/out.json
chmod 600 /box/say/out.json

RUN_NONCE="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
RUN_COUNT=300
NEED_MON=1
export RUN_NONCE RUN_COUNT NEED_MON

set +e
exec 9>/box/say/out.json
setsid --wait env APPDIR=/box/app TMPDIR=/box/tmp HOME=/box/tmp \
    PYTHONDONTWRITEBYTECODE=1 RUN_NONCE="$RUN_NONCE" RUN_COUNT="$RUN_COUNT" \
  setpriv --reuid=1002 --regid=1002 --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py fd:9
exec 9>&-
python /tests/reap.py 1002
set -e

if RUN_OUT=/box/say/out.json APP_DIR=/box/app PRISTINE_DIR=/pristine \
   pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
