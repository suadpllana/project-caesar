#!/bin/bash
# Verifier entry point.
#
# One rule shapes the order of everything below: the reward, and every input the reward is
# derived from, has to sit where the code the agent wrote cannot reach it. So the reward
# channel is locked and set to 0 before a single line of submitted code is imported; the
# tree that actually executes is assembled by root from a pristine copy with only the four
# declared artifacts laid over it; the requests the submission is graded on are generated
# here, from a nonce made after the agent has already finished, so nothing in the agent's
# tree could have anticipated them; the run happens in its own session, under an
# unprivileged uid, with a wall clock bound, and its survivors are killed afterwards; and
# grading happens last, as root, inside pytest, which never imports anything the submission
# wrote.
#
# The run writes its rows into a directory the unprivileged uid owns. That is deliberate
# and safe: the grader treats that file as hostile input, and the only way a forged row
# passes is by being the row the sealed model independently produced.
set -Eeuo pipefail

install -d -o root -g root -m 700 /logs/verifier
chmod 700 /logs/verifier
chown root:root /logs/verifier
echo 0 > /logs/verifier/reward.txt

# The model, the ground truth, the generator and the grader are root-only. The uid that
# runs submitted code cannot open any of them.
chown root:root /tests/gt.json /tests/oracle.py /tests/gen.py /tests/test_outputs.py
chmod 600 /tests/gt.json /tests/oracle.py /tests/gen.py /tests/test_outputs.py

rm -rf /lab
install -d -o root -g root -m 755 /lab

# Pristine tree plus the declared artifacts. A declared file the agent never wrote is
# simply absent, and the shipped one stands in its place.
python /tests/lay.py --pristine /pristine --agent /app --into /lab/tree

NONCE="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
printf '%s' "$NONCE" > /lab/nonce
chown root:root /lab/nonce
chmod 600 /lab/nonce

python /tests/mkcases.py --nonce "$NONCE" --into /lab/req

chown -R root:root /lab/tree /lab/req
chmod -R u=rwX,go=rX /lab/tree /lab/req
install -d -o probe -g probe -m 700 /lab/out

set +e
setsid --wait env HOME=/lab/out TMPDIR=/lab/out PYTHONDONTWRITEBYTECODE=1 \
    setpriv --reuid=1003 --regid=1003 --clear-groups \
    timeout --signal=KILL 900 \
    python /tests/runner.py /lab/tree /lab/req /lab/out/rows.txt
python /tests/reap.py 1003
set -e

if LAB=/lab PRISTINE=/pristine AGENT=/app \
   pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
