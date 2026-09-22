#!/bin/bash
# Two stages, trusting each other in one direction only.
#
#   stage one   runs the submitted list service, unprivileged, and writes down what every
#               graded list file printed. It decides nothing at all.
#   stage two   runs as root, executes not one line of the submission, and reads stage
#               one's output as hostile input.
#
# The reward is 0 until both stages have come back clean, and root writes it last.
set -euo pipefail

UID_SANDBOX=1002
DIR_REWARD=/logs/verifier
DIR_SANDBOX=/work
SECONDS_RUN=60
PER_FAMILY=40

# The reward channel and the sealed side are shut before anything submitted exists in this
# container. Root owns both and 0700 keeps the sandbox uid out of them even if something
# it started outlives the call below.
install -d -m 700 "${DIR_REWARD}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn here, with the agent's container already gone, so nothing that was
# submitted has seen the list files it is about to be graded on. Stage two keeps the
# authoritative copy in the root-owned directory; stage one is given its own, which it may
# rewrite without shrinking the exam it is actually marked against.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${DIR_REWARD}/nonce"
printf '%s\n' "${PER_FAMILY}" > "${DIR_REWARD}/per"
install -d -m 755 -o "${UID_SANDBOX}" -g "${UID_SANDBOX}" "${DIR_SANDBOX}"
install -m 644 -o "${UID_SANDBOX}" -g "${UID_SANDBOX}" \
    "${DIR_REWARD}/nonce" "${DIR_REWARD}/per" "${DIR_SANDBOX}/"

stage_one=0
setpriv --reuid="${UID_SANDBOX}" --regid="${UID_SANDBOX}" --clear-groups \
    timeout "${SECONDS_RUN}" setsid --wait \
    python3 /tests/worker.py --out "${DIR_SANDBOX}/worker_out.json" || stage_one=$?
printf 'stage one exited %s\n' "${stage_one}"

python3 /tests/reap.py || true

stage_two=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${DIR_REWARD}/ctrf.json" || stage_two=$?

if [ "${stage_one}" -eq 0 ] && [ "${stage_two}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
