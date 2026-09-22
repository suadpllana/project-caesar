#!/bin/bash
# Two stages that trust each other in one direction only.
#
#   stage one   runs the submitted lock manager as an unprivileged user over every graded
#               script and records what each one printed; it decides nothing
#   stage two   runs as root, executes no line of the submission, and reads the record of
#               stage one as hostile input
#
# The reward starts at 0 and becomes 1 only when both stages came back clean.
set -euo pipefail

SANDBOX_UID=1002
REWARD_DIR=/logs/verifier
SANDBOX_DIR=/work
RUN_SECONDS=600
PER_FAMILY=40

# Root owns the reward channel and the sealed side, and both are closed to the sandbox uid
# before any submitted line runs - a survivor of stage one finds them closed too.
install -d -m 700 "${REWARD_DIR}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn now, with the agent's container gone, so no submission has seen the
# scripts it is about to be graded on. Stage two keeps the authoritative copy; stage one
# gets its own, which it may scribble on without shrinking the set it is marked against.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${REWARD_DIR}/nonce"
printf '%s\n' "${PER_FAMILY}" > "${REWARD_DIR}/per"
install -d -m 755 -o "${SANDBOX_UID}" -g "${SANDBOX_UID}" "${SANDBOX_DIR}"
install -m 644 -o "${SANDBOX_UID}" -g "${SANDBOX_UID}" \
    "${REWARD_DIR}/nonce" "${REWARD_DIR}/per" "${SANDBOX_DIR}/"

stage_one=0
setpriv --reuid="${SANDBOX_UID}" --regid="${SANDBOX_UID}" --clear-groups \
    timeout "${RUN_SECONDS}" setsid --wait \
    python3 /tests/worker.py --out "${SANDBOX_DIR}/worker_out.json" || stage_one=$?
printf 'stage one exited %s\n' "${stage_one}"

python3 /tests/reap.py || true

stage_two=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${REWARD_DIR}/ctrf.json" || stage_two=$?

if [ "${stage_one}" -eq 0 ] && [ "${stage_two}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
