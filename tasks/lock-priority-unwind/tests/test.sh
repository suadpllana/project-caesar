#!/bin/bash
# Verifier entry point.
#
# The sequence below is the design, not housekeeping. Before a single line the agent wrote is
# executed, the reward file exists, belongs to root, is unreachable from the run and says 0, so
# failure is the default and the channel that would change it is out of reach. The scheduler
# then runs as an unprivileged uid in a session of its own, which is what makes anything it
# double forks reapable, and it reports through a descriptor root opened for it rather than
# through a path it could substitute.
#
# The seed for the drawn task sets is minted here, once per run. The run is handed it, because
# it has to build the same task sets the grader will, and it is handed it at the moment it
# starts. That is the point: no schedule for those task sets could have been worked out earlier
# and written into the submission.
set -Eeuo pipefail

RUN_NONCE="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
SCEN_SEED="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
export RUN_NONCE SCEN_SEED

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

# Only the declared file is taken across. One the agent never wrote simply is not there.
for rel in rt/prio.py; do
  if [ -f "/app/$rel" ]; then
    cp -f "/app/$rel" "/work/app/$rel"
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
