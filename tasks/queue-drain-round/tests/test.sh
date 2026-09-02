#!/bin/bash
# Verifier entry point.
#
# Read this in the order it runs, because the order is the point. The reward channel is shut
# and written to deny before a single byte a submission produced is copied anywhere, so a run
# that hangs, dies, or is killed off leaves a 0 behind and not an absence for somebody to
# interpret. The nonce that decides which streams exist is made next, out of /dev/urandom, in
# this container, after the submission is sealed. Only then is a work tree built.
#
# The run itself owns nothing it is graded on. Its tree belongs to an unprivileged uid and is
# a copy, so the shipped one is untouchable; its report leaves down descriptor 8, which root
# opens here into a directory the run cannot enter; and grading happens afterwards, as root,
# reading that report as hostile input without importing a line of what ran.
set -euo pipefail

say() { echo "[test] $*"; }

VERDICT=/logs/verifier
DROP=/say
TREE=/work/app
LOW=1002
MANY=300

install -d -m 700 "$VERDICT"
echo 0 > /logs/verifier/reward.txt
chmod 0600 /logs/verifier/reward.txt

head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > /tests/nonce
chmod 0600 /tests/nonce

rm -rf /work "$DROP"
install -d -m 755 /work
install -d -m 700 "$DROP"
cp -a /pristine "$TREE"

for name in drn gvp rnd due; do
  if [ -f "/app/house/${name}.py" ]; then
    cp "/app/house/${name}.py" "$TREE/house/${name}.py"
    say "took /app/house/${name}.py"
  else
    say "/app/house/${name}.py was not produced, so the shipped one stands"
  fi
done
find /work -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
chown -R "$LOW:$LOW" /work

: > "$DROP/out.json"
chmod 0600 "$DROP/out.json"

exec 8>"$DROP/out.json"
setsid --wait env \
    APPDIR="$TREE" \
    QDR_NONCE="$(cat /tests/nonce)" \
    QDR_COUNT="$MANY" \
    OUTFD=8 \
    REQUIRE_MONITORING=1 \
    HOME=/tmp \
    PYTHONDONTWRITEBYTECODE=1 \
  setpriv --reuid="$LOW" --regid="$LOW" --clear-groups \
  timeout --signal=KILL 600 python3 /tests/runner.py || say "the run exited nonzero"
exec 8>&-

python3 /tests/reap.py "$LOW" || true

if QDR_REPORT="$DROP/out.json" QDR_WORK="$TREE" QDR_COUNT="$MANY" \
   python3 -m pytest -q --ctrf "$VERDICT/ctrf.json" --rootdir /tests /tests/test_outputs.py; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
chmod 0600 /logs/verifier/reward.txt
exit 0
