#!/bin/bash
# Verifier entry point.
#
# The reward channel is locked and defaulted to 0 before anything the agent wrote is
# executed. The loop run happens in /driver/runner.py as an unprivileged uid, in its own
# session so double-forked survivors can be reaped, under a wall clock timeout, and its
# result lands in a sandbox-writable work file. Grading happens afterwards, as root, in
# pytest, which never executes agent code and reads the ground truth from a root-only
# file the run could not open.
#
# The two PYTHONPATHs below are the point of the split. The run gets /driver, which holds
# the driver and the scenario set. The grader gets /tests, which holds the ground truth
# and the sealed replay that reproves it - and a replay that can be imported is an answer
# key whether or not gt.json is readable, so the run is never given that path.
#
# The meter is the third trust level. It runs as root for the whole of the run, serves
# the encoder and the network over /meter/sock, and records what it was asked for into
# /tests/tape.jsonl. That tape is what the accounting is graded from, so the evidence of
# work done is collected outside the process that did it: a counter, a record or a report
# living in the run is state the submission owns, and an earlier build was passed by a
# probe that owned it.
set -Eeuo pipefail

mkdir -p /logs/verifier
chown root:root /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown -R root:root /tests
chmod 700 /tests
chmod 600 /tests/gt.json

# The meter comes up before anything the agent wrote is executed, and it is the only
# route from text to ids the run has that leaves a record. It serves the sealed encoder
# and the network over the socket, as root, and writes down what it was asked for on the
# privileged side, where the run can neither read it nor edit it. A run that answers the
# scenarios without asking leaves an empty tape, which is graded as what it is.
rm -f /tests/tape.jsonl
mkdir -p /meter
chown root:root /meter
chmod 755 /meter
rm -f /meter/sock
PYTHONPATH=/tests python /tests/meter.py /meter/sock /tests/tape.jsonl &
METER=$!
for _ in $(seq 1 200); do
  [ -S /meter/sock ] && break
  sleep 0.05
done
if [ ! -S /meter/sock ]; then
  echo "the meter did not come up; refusing to grade a run it could not measure" >&2
  exit 1
fi

rm -rf /work
mkdir -p /work/app
cp -a /pristine/. /work/app/

# Overlay only the declared editable files. A file the agent never produced simply is
# not there, and the pristine copy stands.
for f in tok/inc.py tok/store.py loop/ep.py loop/rec.py; do
  if [ -f "/app/$f" ]; then
    cp -f "/app/$f" "/work/app/$f"
  fi
done
find /work/app -name '__pycache__' -type d -prune -exec rm -rf {} +
chown -R sandbox:sandbox /work
chmod 755 /work

set +e
setsid --wait env APPDIR=/work/app PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/driver \
  setpriv --reuid=1002 --regid=1002 --clear-groups \
  timeout --signal=KILL 600 python /driver/runner.py /work/out.json
python /tests/reap.py 1002
kill "$METER" 2>/dev/null
wait "$METER" 2>/dev/null
set -e

# Nothing may reach the tape between the run ending and the grading starting.
rm -f /meter/sock
touch /tests/tape.jsonl
chown root:root /tests/tape.jsonl
chmod 600 /tests/tape.jsonl

if PYTHONPATH=/tests pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
