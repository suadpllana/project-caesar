#!/bin/bash
# Grading runs in two stages, and trust flows one way only.
#
#   stage one   executes the submitted replay engine, unprivileged, and writes down what
#               every graded run file printed. It decides nothing.
#   stage two   runs as root, executes nothing that was submitted, and treats stage one's
#               record as hostile input.
#
# The reward starts at 0 and is raised only when both stages came back clean.
set -euo pipefail

PLAIN_UID=1002
REWARD=/logs/verifier
SCRATCH=/work
CLOCK=60
PER=40

# Shut the reward channel and the sealed side before anything submitted runs. Root owns
# both, and 0700 keeps the unprivileged uid out even if something outlives the call.
install -d -m 700 "${REWARD}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn here, once the agent's container is gone, so nothing that was submitted
# has seen the run files it is about to be graded on. Stage two keeps the authoritative copy
# in the root-owned directory; stage one gets its own, which it is free to rewrite without
# shrinking the exam it is actually marked against.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${REWARD}/seed"
printf '%s\n' "${PER}" > "${REWARD}/per"
install -d -m 755 -o "${PLAIN_UID}" -g "${PLAIN_UID}" "${SCRATCH}"
install -m 644 -o "${PLAIN_UID}" -g "${PLAIN_UID}" "${REWARD}/seed" "${REWARD}/per" "${SCRATCH}/"

stage_one=0
setpriv --reuid="${PLAIN_UID}" --regid="${PLAIN_UID}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --out "${SCRATCH}/stage_one.json" || stage_one=$?
printf 'stage one exited %s\n' "${stage_one}"

python3 /tests/reap.py || true

stage_two=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${REWARD}/ctrf.json" || stage_two=$?

if [ "${stage_one}" -eq 0 ] && [ "${stage_two}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
