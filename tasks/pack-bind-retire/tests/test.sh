#!/bin/bash
# Verifier entry point.
#
# The order below is the whole of the isolation, and every line of it is mechanical: the
# reward channel is root-owned and set to 0 before a single line of submitted code is read;
# the tree that executes is assembled by root from the pristine copy with only the five
# declared artifacts laid over it; the scripts that decide the grade are written here from a
# nonce made after the agent has already stopped; the run happens in its own session under
# an unprivileged uid with a wall clock far above anything the work needs; survivors are
# killed by walking /proc; and grading happens last, as root, inside pytest, which imports
# nothing the submission wrote.
#
# Nothing here inspects how the ledger was computed. It does not need to: a ledger for
# scripts that did not exist when the agent finished is evidence on its own.
set -Eeuo pipefail

install -d -o root -g root -m 700 /logs/verifier
chown root:root /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown root:root /tests/gt.json /tests/model.py /tests/gen.py /tests/cases.py /tests/test_outputs.py
chmod 600 /tests/gt.json /tests/model.py /tests/gen.py /tests/cases.py /tests/test_outputs.py

rm -rf /lab
install -d -o root -g root -m 755 /lab

python /tests/place.py --pristine /pristine --agent /app --into /lab/tree

SEED="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
printf '%s' "$SEED" > /lab/seed
chown root:root /lab/seed
chmod 600 /lab/seed

python /tests/mkcases.py --nonce "$SEED" --count 300 --into /lab/case

chown -R root:root /lab/tree /lab/case
chmod -R u=rwX,go=rX /lab/tree /lab/case
install -d -o walker -g walker -m 700 /lab/out

set +e
setsid --wait env HOME=/lab/out TMPDIR=/lab/out PYTHONDONTWRITEBYTECODE=1 \
    setpriv --reuid=1007 --regid=1007 --clear-groups \
    timeout --signal=KILL 600 \
    python /tests/runner.py /lab/tree /lab/case /lab/out/rows.txt
python /tests/reap.py 1007
set -e

if LAB=/lab PRISTINE=/pristine \
   pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
