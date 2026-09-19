#!/bin/bash
# Grading runs in two passes. The first executes the submitted feeder and is trusted for
# nothing; the second reads what came out of it, as root, and never runs a line of it. The
# reward is raised only when both passes come back clean.
set -euo pipefail

SEAL=/tests/seal
SAND=1002
CLOCK=60
EACH=45
RECORD=/work/worker_out.json

# The reward channel and the answers are put out of reach before the first pass starts, never
# after it. A background process the submission leaves behind therefore has nothing to write.
install -d -m 700 /logs/verifier
chmod 700 "${SEAL}"
echo 0 > /logs/verifier/reward.txt

# The seed is drawn here, with the agent container already gone, so no submission has seen the
# plans it is about to be marked on. The grader keeps this pair; the sandbox is given a copy of
# its own, which it may rewrite as freely as it likes without shrinking its own exam.
python3 - > /logs/verifier/nonce <<'PY'
import secrets

print(secrets.token_hex(16))
PY
printf '%s\n' "${EACH}" > /logs/verifier/per
install -d -m 755 -o "${SAND}" -g "${SAND}" /work
install -m 644 -o "${SAND}" -g "${SAND}" /logs/verifier/nonce /work/nonce
install -m 644 -o "${SAND}" -g "${SAND}" /logs/verifier/per /work/per

first=0
setpriv --reuid="${SAND}" --regid="${SAND}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --out "${RECORD}" || first=$?
echo "worker exit ${first}"

# A double fork leaves the session and the clock behind. It does not leave the uid behind.
python3 /tests/reap.py || true

second=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf /logs/verifier/ctrf.json || second=$?

if [ "${first}" -eq 0 ] && [ "${second}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
