#!/bin/bash
# Two stages, and trust runs one way only.
#
# Stage one executes the submitted rebuild engine as an unprivileged user and writes down
# what each graded program printed. It judges nothing. Stage two runs as root, never executes
# a line of the submission, and treats stage one's file as input from an adversary.
#
# The reward starts at 0 and only a clean run of both stages raises it.
set -euo pipefail

LOW_UID=1002
VERDICT_DIR=/logs/verifier
SCRATCH=/work
CLOCK=60
PER_FAMILY=34

# Everything root owns is locked before a submitted line runs: the directory the reward lives
# in, so a survivor cannot write it afterwards, and the sealed model and frozen answers, so
# code running here cannot read the answers it is being marked against.
install -d -m 700 "${VERDICT_DIR}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn now, with the agent's container already gone, so nothing that was
# submitted has seen the programs it is about to be marked on. Stage two keeps the copy it
# marks against here; stage one gets its own in the scratch directory, which it is free to
# rewrite without shrinking the exam.
install -d -m 755 -o "${LOW_UID}" -g "${LOW_UID}" "${SCRATCH}"
python3 -c "import secrets; print(secrets.token_hex(16))" > "${VERDICT_DIR}/nonce"
printf '%s\n' "${PER_FAMILY}" > "${VERDICT_DIR}/per"
install -m 644 -o "${LOW_UID}" -g "${LOW_UID}" \
    "${VERDICT_DIR}/nonce" "${VERDICT_DIR}/per" "${SCRATCH}/"

stage_one=0
setpriv --reuid="${LOW_UID}" --regid="${LOW_UID}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --out "${SCRATCH}/worker_out.json" || stage_one=$?
printf 'stage one exited %s\n' "${stage_one}"

python3 /tests/reap.py || true

stage_two=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${VERDICT_DIR}/ctrf.json" || stage_two=$?

if [ "${stage_one}" -eq 0 ] && [ "${stage_two}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
