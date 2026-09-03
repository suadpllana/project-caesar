#!/bin/bash
# Verifier entry point.
#
# One rule shapes every line: the reward, and everything it is derived from, has to live where
# executed agent code cannot write. Reading downwards, that means the reward channel is shut and
# defaulted before anything the agent wrote is loaded; the executed tree is a root-owned copy of
# the shipped server with only the four declared artifacts laid over it; the report the run writes
# is opened by root and passed in as an inherited descriptor, so the uid running agent code never
# owns the file it is graded on; the run gets its own session and a wall clock and whatever it
# leaves behind is reaped; and grading is a separate root process that imports none of it.
#
# The nonce below is made after the agent has finished and seeds the three hundred jobs the
# submission is really graded on. Both sides are handed it, so the run and the grader are talking
# about the same jobs.
set -Eeuo pipefail

readonly LOGS=/logs/verifier
readonly WORK=/work
readonly SEALED="/tests/gt.json /tests/oracle.py /tests/test_outputs.py"

mkdir -p "${LOGS}"
chown root:root "${LOGS}"
chmod 700 "${LOGS}"
echo 0 > /logs/verifier/reward.txt

chown root:root ${SEALED}
chmod 600 ${SEALED}

rm -rf "${WORK}"
mkdir -p "${WORK}/app" "${WORK}/run"
cp -a /pristine/. "${WORK}/app/"

overlay() {
  local rel
  for rel in "$@"; do
    [ -f "/app/${rel}" ] && cp -f "/app/${rel}" "${WORK}/app/${rel}"
  done
  return 0
}
overlay srv/look.py srv/bite.py srv/hold.py srv/pick.py

find "${WORK}/app" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "${WORK}/app" -name '*.pyc' -delete 2>/dev/null || true

chown -R root:root "${WORK}"
chmod -R u=rwX,go=rX "${WORK}/app"
chmod 755 "${WORK}" "${WORK}/run"
install -d -o sandbox -g sandbox -m 700 "${WORK}/scratch"

: > "${WORK}/run/out.json"
chown root:root "${WORK}/run/out.json"
chmod 600 "${WORK}/run/out.json"

RUN_NONCE="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
RUN_COUNT=300
export RUN_NONCE RUN_COUNT

set +e
exec 9>"${WORK}/run/out.json"
setsid --wait env APPDIR="${WORK}/app" TMPDIR="${WORK}/scratch" HOME="${WORK}/scratch" \
    PYTHONDONTWRITEBYTECODE=1 RUN_NONCE="${RUN_NONCE}" RUN_COUNT="${RUN_COUNT}" \
  setpriv --reuid=1002 --regid=1002 --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py fd:9
exec 9>&-
python /tests/reap.py 1002
set -e

# REQUIRE_MONITORING is deliberately not set. The grader honours it and would insist the
# interpreter's own instrumentation was used rather than the profile hook, but it adds nothing
# here: whichever mechanism was armed, the grader already requires it to have still been armed
# when the run ended and requires the interpreter's tally of driver and tool entries to match what
# the traces claim. Forcing the fallback evades neither. Set it only after watching the reference
# pass the two-image trial with it on.
if RUN_OUT="${WORK}/run/out.json" APP_DIR="${WORK}/app" PRISTINE_DIR=/pristine \
   pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
