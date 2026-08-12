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
set -Eeuo pipefail

mkdir -p /logs/verifier
chown root:root /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown -R root:root /tests
chmod 700 /tests
chmod 600 /tests/gt.json

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
set -e

if PYTHONPATH=/tests pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
