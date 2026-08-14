#!/bin/bash
# Verifier entry point.
#
# The reward channel is locked and defaulted to 0 before anything the agent wrote is
# executed. The engine run happens in /tests/runner.py as an unprivileged uid, in its own
# session so double-forked survivors can be reaped, under a wall clock timeout, and its
# result lands in a file that uid cannot open for writing: root opens it and hands the
# descriptor over. Grading happens afterwards, as root, in pytest, which never executes
# agent code and reads the ground truth, the sealed oracle and the scenario config from
# root-only files the run could not open.
#
# The tree the run executes is root-owned and read-only to it. Only /app/view/route.py is
# overlaid onto the pristine copy, so the counters in view/core.py and the edit split in
# view/land.py are the shipped ones - and pytest attests that afterwards rather than
# trusting it.
set -Eeuo pipefail

mkdir -p /logs/verifier
chown root:root /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown root:root /tests/gt.json /tests/oracle.py /tests/test_outputs.py /tests/view.json
chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py
chmod 644 /tests/view.json

rm -rf /work
mkdir -p /work/app /work/run

cp -a /pristine/. /work/app/

# Overlay only the declared editable file. A file the agent never produced simply is
# not there, and the pristine copy stands.
for f in view/route.py; do
  if [ -f "/app/$f" ]; then
    cp -f "/app/$f" "/work/app/$f"
  fi
done
find /work/app -name '__pycache__' -type d -prune -exec rm -rf {} +

# The run reads the engine and writes nothing into it. Anything it does write goes to a
# scratch directory that is graded against nothing.
chown -R root:root /work
chmod -R u=rwX,go=rX /work/app
chmod 755 /work /work/run
install -d -o sandbox -g sandbox -m 700 /work/scratch

: > /work/run/out.json
chown root:root /work/run/out.json
chmod 600 /work/run/out.json

RUN_NONCE="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
export RUN_NONCE

set +e
exec 3>/work/run/out.json
setsid --wait env APPDIR=/work/app TMPDIR=/work/scratch PYTHONDONTWRITEBYTECODE=1 \
  RUN_NONCE="$RUN_NONCE" \
  setpriv --reuid=1002 --regid=1002 --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py fd:3
exec 3>&-
python /tests/reap.py 1002
set -e

if RUN_OUT=/work/run/out.json APP_DIR=/work/app PRISTINE_DIR=/pristine ARTIFACT_DIR=/app \
   REQUIRE_MONITORING=1 \
   pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
