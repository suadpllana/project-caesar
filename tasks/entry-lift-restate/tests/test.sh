#!/bin/bash
# Two stages, and the trust between them runs one way only.
#
#   the run      executes the submitted resolver as an unprivileged uid and writes down what
#                every graded program printed. It judges nothing.
#   the grade     runs as root, executes not one line of the submission, and treats the run's
#                output as hostile input.
#
# The reward is 0 until both stages have come back clean.
set -euo pipefail

SANDBOX_UID=1002
REWARD_DIR=/logs/verifier
SANDBOX_DIR=/work
RUN_SECONDS=60
PER_FAMILY=36

# The reward channel and the sealed side are shut before anything submitted runs. Root owns
# both and 0700 keeps the sandbox uid out, survivors included.
install -d -m 700 "${REWARD_DIR}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn here, once the agent's container is already gone, so nothing that was
# submitted has seen the programs it is about to be marked on. The authoritative copy stays
# in the root-owned directory; the run gets one of its own, which it is free to rewrite
# without changing the exam it is actually marked against.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${REWARD_DIR}/nonce"
printf '%s\n' "${PER_FAMILY}" > "${REWARD_DIR}/per"
install -d -m 755 -o "${SANDBOX_UID}" -g "${SANDBOX_UID}" "${SANDBOX_DIR}"
install -m 644 -o "${SANDBOX_UID}" -g "${SANDBOX_UID}" \
    "${REWARD_DIR}/nonce" "${REWARD_DIR}/per"  "${SANDBOX_DIR}/"

run_status=0
setpriv --reuid="${SANDBOX_UID}" --regid="${SANDBOX_UID}" --clear-groups \
    timeout "${RUN_SECONDS}" setsid --wait \
    python3 /tests/worker.py --out "${SANDBOX_DIR}/worker_out.json" || run_status=$?
printf 'the run exited %s\n' "${run_status}"

python3 /tests/reap.py || true

grade_status=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${REWARD_DIR}/ctrf.json" || grade_status=$?

if [ "${run_status}" -eq 0 ] && [ "${grade_status}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
