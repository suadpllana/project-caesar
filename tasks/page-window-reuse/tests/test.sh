#!/bin/bash
# Two stages, and the reward comes from the second one only.
#
# The first stage runs what the agent wrote. It is unprivileged, in a session of its own,
# under the clock the brief states, and it is trusted for nothing: all it does is write down
# what the service printed. The second stage grades that record as root and never runs a line
# of agent code. Both have to come back clean for the reward to be raised, and everything the
# reward is derived from is out of the first stage's reach before it starts.
set -euo pipefail

SEAL=/tests/seal
WORK=/work
LOGS=/logs/verifier
SANDBOX=1002
CLOCK=60
PER=39

# Reward channel first: root-owned, 700, and already holding a 0. A process the submission
# leaves behind cannot write it afterwards, and a crash anywhere below leaves the 0 standing.
install -d -m 700 "${LOGS}"
echo 0 > /logs/verifier/reward.txt
chmod 700 "${SEAL}"

# The exam is drawn now, after the agent's container is gone, so no submission has seen the
# programs it will be graded on. The grader reads the pair from ${LOGS}; the worker gets its
# own copy under ${WORK}, which it may rewrite without shrinking its own exam.
python3 -c 'import secrets; print(secrets.token_hex(16))' > "${LOGS}/nonce"
echo "${PER}" > "${LOGS}/per"
install -d -m 755 -o "${SANDBOX}" -g "${SANDBOX}" "${WORK}"
install -m 644 -o "${SANDBOX}" -g "${SANDBOX}" "${LOGS}/nonce" "${LOGS}/per" "${WORK}/"

worker=0
setpriv --reuid="${SANDBOX}" --regid="${SANDBOX}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --out "${WORK}/worker_out.json" || worker=$?
echo "worker stage exit ${worker}"

# A double fork walks out of the session and out of the clock. Out of the uid it does not.
python3 /tests/reap.py "${SANDBOX}" || true

grader=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${LOGS}/ctrf.json" || grader=$?
echo "grading stage exit ${grader}"

if [ "${worker}" = "0" ] && [ "${grader}" = "0" ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
