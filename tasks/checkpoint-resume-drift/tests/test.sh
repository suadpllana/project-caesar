#!/bin/bash
# Verifier entry point.
#
# The reward channel is locked and defaulted to 0 before anything the agent wrote is
# executed. The trainer run happens in /tests/runner.py as an unprivileged uid, in its own
# session so double-forked survivors can be reaped, under a wall clock timeout, and its
# result lands in a sandbox-writable work file. Grading happens afterwards, as root, in
# pytest, which never executes agent code and reads the ground truth and the sealed
# trainer from root-only files the run could not open.
set -Eeuo pipefail

mkdir -p /logs/verifier
chown root:root /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown root:root /tests/gt.json /tests/oracle.py
chmod 600 /tests/gt.json /tests/oracle.py

rm -rf /work
mkdir -p /work/app
cp -a /pristine/. /work/app/

# Overlay only the declared editable files. A file the agent never produced simply is
# not there, and the pristine copy stands.
for f in train/ckpt.py data/feed.py train/noise.py train/sched.py; do
  if [ -f "/app/$f" ]; then
    cp -f "/app/$f" "/work/app/$f"
  fi
done
find /work/app -name '__pycache__' -type d -prune -exec rm -rf {} +
chown -R sandbox:sandbox /work
chmod 755 /work

set +e
setsid --wait env APPDIR=/work/app PYTHONDONTWRITEBYTECODE=1 \
  setpriv --reuid=1002 --regid=1002 --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py /work/out.json
python /tests/reap.py 1002
set -e

if pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
