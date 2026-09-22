#!/bin/bash
# Grading has two halves and the trust runs one way only.
#
#   half one   runs the submitted cache, unprivileged and time-bounded, and records what
#              every graded program printed. It reaches no verdict.
#   half two   runs as root, executes nothing the agent wrote, and treats half one's record
#              as input from a stranger.
#
# The reward is 0 until both halves have come back clean.
set -euo pipefail

PEN=1002
PAID=/logs/verifier
DESK=/work
CLOCK=60
PER_FAMILY=40

# The reward channel and the sealed side are shut before anything submitted runs. Root owns
# both and 0700 keeps the sandbox uid out even if something it started outlives the call.
install -d -m 700 "${PAID}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn here, with the agent's container already gone, so no submission has seen
# the programs it is about to be marked on. Half two keeps the authoritative copy in the
# root-owned directory and hands half one its own, which half one may rewrite without
# shrinking the set it is actually marked against.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${PAID}/nonce"
printf '%s\n' "${PER_FAMILY}" > "${PAID}/per"
install -d -m 755 -o "${PEN}" -g "${PEN}" "${DESK}"
install -m 644 -o "${PEN}" -g "${PEN}" "${PAID}/nonce" "${PAID}/per" "${DESK}/"

half_one=0
setpriv --reuid="${PEN}" --regid="${PEN}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --out "${DESK}/said.json" || half_one=$?
printf 'half one exited %s\n' "${half_one}"

python3 /tests/reap.py || true

half_two=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${PAID}/ctrf.json" || half_two=$?

if [ "${half_one}" -eq 0 ] && [ "${half_two}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
