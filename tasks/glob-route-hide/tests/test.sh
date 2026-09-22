#!/bin/bash
# Two stages that trust each other in one direction only.
#
#   the worker   runs the submitted resolver over the exam as an unprivileged uid, under the
#                task's 60 second clock, and writes down what every program printed. It
#                decides nothing.
#   the grader   runs as root, never executes submitted code, rebuilds the exam from the seed
#                and reads the worker's record as hostile input.
#
# The reward is 0 from the first line and becomes 1 only when both stages came back clean.
set -euo pipefail

SANDBOX=1002
LOGS=/logs/verifier
EXAM=/exam
WORK=/work
CLOCK=60
PER=40

# Lock the reward channel and the sealed side before anything submitted can run.
install -d -m 700 "${LOGS}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn now, after the agent's container is gone. Only root ever holds it; the
# worker gets the programs, written by root into a directory it can read and not change.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${LOGS}/nonce"
echo "${PER}" > "${LOGS}/per"
rm -rf "${EXAM}"
install -d -m 755 "${EXAM}"
python3 /tests/exam.py --seed "$(cat "${LOGS}/nonce")" --per "${PER}" --out "${EXAM}"
chmod 644 "${EXAM}"/*
install -d -m 755 -o "${SANDBOX}" -g "${SANDBOX}" "${WORK}"

ran=0
setpriv --reuid="${SANDBOX}" --regid="${SANDBOX}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --exam "${EXAM}" --out "${WORK}/worker_out.json" || ran=$?
echo "worker exited ${ran}"
python3 /tests/reap.py || true

judged=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${LOGS}/ctrf.json" || judged=$?

if [ "${ran}" -eq 0 ] && [ "${judged}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
