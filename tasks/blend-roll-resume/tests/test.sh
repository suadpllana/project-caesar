#!/bin/bash
# The graded run, in two stages that trust each other with nothing.
#
# Stage one executes what the agent submitted. It runs as an unprivileged uid, in a session of
# its own, under the wall clock that is also the task's stated execution limit, and everything
# it produces is treated afterwards as hostile input.
#
# Stage two grades, as root, and never runs a line of agent code. The reward is 0 unless both
# stages come back clean, and it is written last, by this shell, into a directory the first
# stage was locked out of before it started.
set -euo pipefail

LOGS=/logs/verifier
WORK=/work
SEAL=/tests/seal
SANDBOX=1002
CLOCK=60
PER_FAMILY=45

# 1. Shut the reward channel and the sealed answers before anything of the agent's runs.
install -d -m 700 "${LOGS}"
echo 0 > /logs/verifier/reward.txt
chmod 700 "${SEAL}"

# 2. Draw the exam. The seed is taken now, with the agent's container already gone, so no
#    submission can have been fitted to the scripts it is about to be graded on. The grader
#    keeps its copy in ${LOGS}; the worker gets its own under ${WORK} and is welcome to
#    rewrite that one, which only costs it the scripts the grader will still ask for.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${LOGS}/nonce"
printf '%s\n' "${PER_FAMILY}" > "${LOGS}/per"
install -d -m 755 -o "${SANDBOX}" -g "${SANDBOX}" "${WORK}"
install -m 644 -o "${SANDBOX}" -g "${SANDBOX}" "${LOGS}/nonce" "${WORK}/nonce"
install -m 644 -o "${SANDBOX}" -g "${SANDBOX}" "${LOGS}/per" "${WORK}/per"

# 3. Run the submitted feed. Its exit status is kept: a crash, a hang or a quiet exit is a
#    failure and never a pass by default.
worker_status=0
setpriv --reuid="${SANDBOX}" --regid="${SANDBOX}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --out "${WORK}/worker_out.json" || worker_status=$?
echo "stage one exited ${worker_status}"

# 4. A double fork walks out of the session and out of the clock. It does not walk out of its uid.
python3 /tests/reap.py || true

# 5. Grade.
grader_status=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${LOGS}/ctrf.json" || grader_status=$?
echo "stage two exited ${grader_status}"

if [ "${worker_status}" -eq 0 ] && [ "${grader_status}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
