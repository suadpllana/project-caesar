#!/bin/bash
# The reward is written once, by this script, after both stages have come back clean. Stage one
# runs the submitted service and decides nothing; stage two grades it as root and runs none of
# it. Anything else - a crash, the clock, an unreadable record - leaves the 0 that is written
# here before the submitted code exists in this container.
set -euo pipefail

LOGS=/logs/verifier
WORK=/work
SANDBOX=1002
CLOCK=60
FAMILY=45

lock_the_reward_channel() {
  install -d -m 700 "${LOGS}"
  echo 0 > /logs/verifier/reward.txt
  chmod 700 /tests/seal
}

draw_the_exam() {
  # After the agent's container is gone, so no submission has seen the programs it is graded on.
  # The grader keeps its copy in ${LOGS}; the worker is handed its own under ${WORK} and may
  # rewrite that without shrinking the set it is actually judged against.
  python3 -c "import secrets; print(secrets.token_hex(16))" > "${LOGS}/nonce"
  printf '%s\n' "${FAMILY}" > "${LOGS}/per"
  install -d -m 755 -o "${SANDBOX}" -g "${SANDBOX}" "${WORK}"
  install -m 644 -o "${SANDBOX}" -g "${SANDBOX}" "${LOGS}/nonce" "${WORK}/nonce"
  install -m 644 -o "${SANDBOX}" -g "${SANDBOX}" "${LOGS}/per" "${WORK}/per"
}

lock_the_reward_channel
draw_the_exam

worker=0
setpriv --reuid="${SANDBOX}" --regid="${SANDBOX}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --out "${WORK}/worker_out.json" || worker=$?
echo "worker exit ${worker}"

python3 /tests/reap.py || true

grader=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${LOGS}/ctrf.json" || grader=$?
echo "grader exit ${grader}"

if [ "${worker}" -eq 0 ] && [ "${grader}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
