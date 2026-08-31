#!/bin/bash
# Verifier entry point.
#
# Order matters here and every line of it is a consequence of one rule: the reward, and
# everything the reward is derived from, has to live where the executed agent code cannot
# write. So the reward channel is locked and defaulted to 0 before anything the agent
# wrote is loaded; the runtime tree the run executes is root-owned and read-only to it,
# with only the four declared artifacts overlaid onto a pristine copy; the file the run
# reports into is opened by root and handed over as an inherited descriptor after the
# privilege drop, so the uid running agent code does not own the file it is graded on;
# the run happens in its own session under a wall clock timeout and survivors are reaped;
# and grading happens afterwards, as root, in pytest, which never executes agent code and
# reads the sealed model and the ground truth from files the run could not open.
#
# The nonce is made here, after the agent has finished, and it seeds the three hundred
# programs the submission is actually graded on. It is exported to both sides so the run
# and the grader are answering about the same programs.
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

# Only the declared artifacts are overlaid. One the agent never wrote simply is not
# there, and the shipped file stands.
for rel in kern/pick.py kern/stop.py kern/knot.py kern/wake.py; do
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
exec 7>/work/run/out.json
setsid --wait env APPDIR=/work/app TMPDIR=/work/scratch HOME=/work/scratch \
    PYTHONDONTWRITEBYTECODE=1 RUN_NONCE="$RUN_NONCE" RUN_COUNT="$RUN_COUNT" \
  setpriv --reuid=1002 --regid=1002 --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py fd:7
exec 7>&-
python /tests/reap.py 1002
set -e

# REQUIRE_MONITORING is deliberately not set. The grader supports it and will insist the
# interpreter's own instrumentation was used rather than the profile hook, but the check it
# adds is redundant here: whichever mechanism is armed, the grader already requires it to
# have been intact at the end of every program and requires the interpreter's count of
# emitter entries to equal the number of trace rows, and neither of those can be evaded by
# forcing the fallback. Turning it on is a tightening, not a fix, and it should only be
# turned on by someone who has run the two-image trial and watched the reference pass with
# it set.
if RUN_OUT=/work/run/out.json APP_DIR=/work/app PRISTINE_DIR=/pristine \
   pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
