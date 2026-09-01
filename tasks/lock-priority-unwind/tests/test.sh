#!/bin/bash
# Verifier entry point.
#
# Order matters here. The reward file is created, locked to root and set to 0 before any line
# the agent wrote is executed, so the default answer is failure and the run cannot reach the
# channel that would change it. The scheduler then runs under an unprivileged uid in a session
# of its own, so anything it double forks can be reaped, and it reports through a descriptor
# opened by root beforehand rather than through a path it could replace.
#
# The seed for the drawn scenarios is minted here, per run. The run is told what it is - it has
# to be, to build the same task sets - but it is told at the moment it starts, which is the
# whole point: there is no schedule for those task sets that anybody could have worked out
# earlier and written into the submission.
set -Eeuo pipefail

mkdir -p /logs/verifier
chown root:root /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown root:root /tests/gt.json /tests/oracle.py /tests/test_outputs.py /tests/sched.json
chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py
chmod 644 /tests/sched.json

rm -rf /work
mkdir -p /work/app /work/box

cp -a /pristine/. /work/app/

# Only the declared file is taken from the agent. A file it never wrote simply is not there.
for f in rt/prio.py; do
  if [ -f "/app/$f" ]; then
    cp -f "/app/$f" "/work/app/$f"
  fi
done
find /work/app -name '__pycache__' -type d -prune -exec rm -rf {} +

chown -R root:root /work
chmod -R u=rwX,go=rX /work/app
chmod 755 /work /work/box
install -d -o sandbox -g sandbox -m 700 /work/tmp

: > /work/box/out.json
chown root:root /work/box/out.json
chmod 600 /work/box/out.json

RUN_NONCE="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
SCEN_SEED="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
export RUN_NONCE SCEN_SEED

set +e
exec 7>/work/box/out.json
setsid --wait env APPDIR=/work/app TMPDIR=/work/tmp PYTHONDONTWRITEBYTECODE=1 \
  RUN_NONCE="$RUN_NONCE" SCEN_SEED="$SCEN_SEED" SCEN_DRAWN=12 \
  setpriv --reuid=1002 --regid=1002 --clear-groups \
  timeout --signal=KILL 420 python /tests/runner.py fd:7
exec 7>&-
python /tests/sweep.py 1002
set -e

if RUN_OUT=/work/box/out.json APP_DIR=/work/app PRISTINE_DIR=/pristine ARTIFACT_DIR=/app \
   RUN_NONCE="$RUN_NONCE" \
   pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
