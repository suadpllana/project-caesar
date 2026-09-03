#!/bin/bash
# Verifier entry point.
#
# The order of the first four lines is the whole security argument: the reward channel is
# root-owned, locked, and set to a default deny before anything the submission wrote is
# copied anywhere, so a run that dies, hangs, or is killed leaves a 0 behind rather than an
# absence somebody has to interpret.
#
# The run then gets a work copy of the pristine tree with the four declared artifacts laid
# over it, owned by an unprivileged uid, in its own session, under a wall clock. Its report
# leaves through descriptor 8, which root opens here and hands down: the uid that executes
# the submission never owns the file it is graded on and cannot reopen it, because /rep is
# root-only. Grading happens afterwards, as root, and reads that report as hostile input
# without importing a line of it.
#
# The nonce is made here, after the submission has stopped, and it seeds the three hundred
# panels the run is actually graded on. Both sides are told the same nonce so the run and
# the grader are answering about the same panels.
set -Eeuo pipefail

LOGS=/logs/verifier
REP=/rep
WORK=/work
UID_RUN=1002

mkdir -p "$LOGS"
chown root:root "$LOGS"
chmod 700 "$LOGS"
echo 0 > /logs/verifier/reward.txt
chmod 600 /logs/verifier/reward.txt

chown root:root /tests/gt.json /tests/oracle.py /tests/test_outputs.py
chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py

rm -rf "$WORK" "$REP"
mkdir -p "$WORK/app" "$REP"
chmod 700 "$REP"

cp -a /pristine/. "$WORK/app/"
for rel in pnl/ord.py pnl/wire.py pnl/trip.py pnl/same.py; do
  if [ -f "/app/$rel" ]; then
    cp -f "/app/$rel" "$WORK/app/$rel"
    echo "[test] took /app/$rel"
  else
    echo "[test] /app/$rel was not produced; the shipped file stands"
  fi
done
find "$WORK" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$WORK" -name '*.pyc' -delete 2>/dev/null || true
chown -R "$UID_RUN:$UID_RUN" "$WORK"

PSO_NONCE="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
PSO_COUNT=300
export PSO_NONCE PSO_COUNT

: > "$REP/out.json"
chown root:root "$REP/out.json"
chmod 600 "$REP/out.json"

set +e
exec 8>"$REP/out.json"
setsid --wait env \
    APPDIR="$WORK/app" \
    PSO_NONCE="$PSO_NONCE" \
    PSO_COUNT="$PSO_COUNT" \
    OUTFD=8 \
    REQUIRE_MONITORING=1 \
    HOME=/tmp \
    TMPDIR=/tmp \
    PYTHONDONTWRITEBYTECODE=1 \
  setpriv --reuid="$UID_RUN" --regid="$UID_RUN" --clear-groups \
  timeout --signal=KILL 600 python3 /tests/runner.py
exec 8>&-
python3 /tests/reap.py "$UID_RUN"
set -e

cd /tests
if PSO_REPORT="$REP/out.json" PSO_TREE="$WORK/app" PSO_PRISTINE=/pristine \
   python3 -m pytest -q --ctrf "$LOGS/ctrf.json" test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
chmod 600 /logs/verifier/reward.txt
exit 0
