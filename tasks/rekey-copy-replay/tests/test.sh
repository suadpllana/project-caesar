#!/bin/bash
# Two halves, trusting each other in one direction only.
#
#   half one   runs the submitted rebuild over every graded program, unprivileged and under a
#              wall clock, and writes down what each one printed. It reaches no verdict.
#   half two   runs as root, executes nothing the submission wrote, and reads half one's file
#              as input from an adversary.
#
# The reward is 0 until both halves have come back clean.
set -euo pipefail

SANDBOX_UID=1002
REWARD_DIR=/logs/verifier
SANDBOX_DIR=/work
RUN_SECONDS=60
PER_FAMILY=36

# Shut the reward channel and the sealed side before a submitted statement can run. Both are
# root-owned and 0700, which holds even against a process that outlives the call.
install -d -m 700 "${REWARD_DIR}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn now, with the agent's container already gone, so nothing that was
# submitted has seen the programs it is about to be marked on. The authoritative copy of the
# seed and of the family size stays in the root-owned directory. Half one is handed its own
# copy, which it is free to rewrite without shrinking the exam half two marks it against.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${REWARD_DIR}/nonce"
printf '%s\n' "${PER_FAMILY}" > "${REWARD_DIR}/per"
install -d -m 755 -o "${SANDBOX_UID}" -g "${SANDBOX_UID}" "${SANDBOX_DIR}"
install -m 644 -o "${SANDBOX_UID}" -g "${SANDBOX_UID}" \
    "${REWARD_DIR}/nonce" "${REWARD_DIR}/per" "${SANDBOX_DIR}/"

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
