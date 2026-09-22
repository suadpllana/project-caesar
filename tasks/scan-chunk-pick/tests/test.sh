#!/bin/bash
# Grading runs in three parts that trust each other in one direction only.
#
#   prep        builds the graded segment files as root, before any clock starts, so the
#               limit the brief states measures the submitted engine and nothing else.
#   worker      executes the submitted scan layer, unprivileged, under that clock, and
#               writes down what every segment file printed. It decides nothing.
#   grader      runs as root, never executes a line of the submission, and reads the
#               worker's output as hostile input.
#
# The reward starts at 0 and is raised only when both of the last two came back clean.
set -euo pipefail

SANDBOX_UID=1002
REWARD_DIR=/logs/verifier
SANDBOX_DIR=/work
RUN_SECONDS=60
PER_FAMILY=22

# Lock the reward channel and the sealed side before anything submitted runs. Root owns both;
# 0700 keeps the sandbox uid out even if it outlives the call.
install -d -m 700 "${REWARD_DIR}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn here, after the agent's container is gone, so nothing that was submitted
# has seen the segment files it is about to be graded on. It stays in the root-owned directory:
# the worker is handed the built files and never the seed they came from.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${REWARD_DIR}/nonce"
printf '%s\n' "${PER_FAMILY}" > "${REWARD_DIR}/per"
install -d -m 755 -o "${SANDBOX_UID}" -g "${SANDBOX_UID}" "${SANDBOX_DIR}"
python3 /tests/prep.py --nonce "${REWARD_DIR}/nonce" --per "${PER_FAMILY}" \
    --out "${SANDBOX_DIR}/progs.json"
chmod 644 "${SANDBOX_DIR}/progs.json"

worker_status=0
setpriv --reuid="${SANDBOX_UID}" --regid="${SANDBOX_UID}" --clear-groups \
    timeout "${RUN_SECONDS}" setsid --wait \
    python3 /tests/worker.py --progs "${SANDBOX_DIR}/progs.json" \
    --out "${SANDBOX_DIR}/worker_out.json" || worker_status=$?
printf 'worker exited %s\n' "${worker_status}"

python3 /tests/reap.py || true

grader_status=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${REWARD_DIR}/ctrf.json" || grader_status=$?

if [ "${worker_status}" -eq 0 ] && [ "${grader_status}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
