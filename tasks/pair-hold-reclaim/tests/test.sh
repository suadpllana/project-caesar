#!/bin/bash
# Verifier entry point.
#
# Order matters here and the first three lines are the reason: the reward channel is
# locked and set to a default deny before anything the submission wrote is copied
# anywhere, so a run that dies, hangs or is killed leaves a 0 behind rather than an
# absence the platform has to interpret.
#
# The run itself gets a work copy of the pristine tree with the four declared artifacts
# laid over it, owned by an unprivileged uid, in its own session, under a wall clock. Its
# report goes through descriptor 9, which root opens here and hands over: the uid that
# executes agent code never owns the file it is graded on, and cannot reopen it, because
# /rep is root-only. Grading happens afterwards, as root, and reads that file as hostile
# input without importing a line of it.
set -euo pipefail

LOGS=/logs/verifier
REP=/rep
WORK=/work
RUNUID=1002

mkdir -p "$LOGS"
chmod 700 "$LOGS"
echo 0 > /logs/verifier/reward.txt
chmod 600 /logs/verifier/reward.txt

rm -rf "$WORK" "$REP"
mkdir -p "$WORK" "$REP"
chmod 700 "$REP"

cp -a /pristine "$WORK/app"
for f in rch.py cln.py pss.py obs.py; do
  if [ -f "/app/core/$f" ]; then
    cp "/app/core/$f" "$WORK/app/core/$f"
    echo "[test] took /app/core/$f"
  else
    echo "[test] /app/core/$f was not produced; the shipped one stands"
  fi
done
find "$WORK" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
chown -R "$RUNUID:$RUNUID" "$WORK"

head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > /tests/nonce
chmod 600 /tests/nonce

: > "$REP/out.json"
chmod 600 "$REP/out.json"

exec 9>"$REP/out.json"
setsid --wait env \
    APPDIR="$WORK/app" \
    PHR_NONCE="$(cat /tests/nonce)" \
    PHR_COUNT=300 \
    OUTFD=9 \
    REQUIRE_MONITORING=1 \
    HOME=/tmp \
    PYTHONDONTWRITEBYTECODE=1 \
  setpriv --reuid="$RUNUID" --regid="$RUNUID" --clear-groups \
  timeout --signal=KILL 600 python3 /tests/runner.py || echo "[test] the run exited nonzero"
exec 9>&-

python3 /tests/reap.py "$RUNUID" || true

cd /tests
if PHR_REPORT="$REP/out.json" python3 -m pytest -q --ctrf "$LOGS/ctrf.json" test_outputs.py; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
chmod 600 /logs/verifier/reward.txt
exit 0
