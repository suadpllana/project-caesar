#!/bin/bash
# Grading runs in two halves that trust each other in one direction only.
#
#   half one    replays every graded document through the submitted pane, unprivileged, and
#               writes down what each one printed. It decides nothing.
#   half two    runs as root, never executes a line of the submission, and reads half one's
#               output as hostile input.
#
# The reward starts at 0 and is raised only when both halves came back clean.
set -euo pipefail

SANDBOX_UID=1002
REWARD_DIR=/logs/verifier
SANDBOX_DIR=/work
RUN_SECONDS=60
PER_FAMILY=35

# Lock the reward channel and the sealed side before anything submitted runs. Root owns both;
# 0700 keeps the sandbox uid out even if it outlives the call.
install -d -m 700 "${REWARD_DIR}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn here, after the agent's container is gone, so nothing that was submitted
# has seen the documents it is about to be graded on. Half two keeps the authoritative copy in
# the root-owned directory; half one gets its own, which it may rewrite without shrinking the
# exam it is actually marked against.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${REWARD_DIR}/nonce"
printf '%s\n' "${PER_FAMILY}" > "${REWARD_DIR}/per"
install -d -m 755 -o "${SANDBOX_UID}" -g "${SANDBOX_UID}" "${SANDBOX_DIR}"
install -m 644 -o "${SANDBOX_UID}" -g "${SANDBOX_UID}" \
    "${REWARD_DIR}/nonce" "${REWARD_DIR}/per"  "${SANDBOX_DIR}/"

worker_status=0
setpriv --reuid="${SANDBOX_UID}" --regid="${SANDBOX_UID}" --clear-groups \
    timeout "${RUN_SECONDS}" setsid --wait \
    python3 /tests/worker.py --out "${SANDBOX_DIR}/worker_out.json" || worker_status=$?
printf 'half one exited %s\n' "${worker_status}"

python3 /tests/reap.py || true

grader_status=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${REWARD_DIR}/ctrf.json" || grader_status=$?

if [ "${worker_status}" -eq 0 ] && [ "${grader_status}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
