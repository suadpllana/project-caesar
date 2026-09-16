#!/bin/bash
# The reward is written once, at the end, by a stage that never runs a line of the submission.
#
# Stage one replays every graded shard through the submitted modules. It runs as an
# unprivileged uid, in a session of its own, under the wall clock that is also this task's
# execution limit, and it is trusted for nothing: everything it writes is treated as hostile
# input by stage two. Stage two grades as root and only both stages coming back clean raise
# the reward.
set -euo pipefail

LOGS=/logs/verifier
WORK=/work
SANDBOX=1002
LIMIT=60
PER_FAMILY=45

# The reward channel and the sealed answers are put out of reach before anything the
# submission wrote is executed, so a process it leaves behind has nowhere to write.
install -d -m 700 "${LOGS}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn now, with the agent's container already gone, so no submission can have
# seen the shards it is about to be graded on. Stage two reads the pair from ${LOGS}, which
# stage one cannot write; stage one gets its own copy under ${WORK} and is welcome to rewrite
# that without shrinking its own exam.
python3 -c 'import secrets; print(secrets.token_hex(16))' > "${LOGS}/nonce"
echo "${PER_FAMILY}" > "${LOGS}/per"
install -d -m 755 -o "${SANDBOX}" -g "${SANDBOX}" "${WORK}"
install -m 644 -o "${SANDBOX}" -g "${SANDBOX}" "${LOGS}/nonce" "${LOGS}/per" "${WORK}/"

replay=0
setpriv --reuid="${SANDBOX}" --regid="${SANDBOX}" --clear-groups \
    timeout "${LIMIT}" setsid --wait \
    python3 /tests/worker.py --out "${WORK}/worker_out.json" || replay=$?
echo "replay stage exit ${replay}"

# A double fork walks out of the session and out of the clock. It does not walk out of its uid.
python3 /tests/reap.py || true

grade=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${LOGS}/ctrf.json" || grade=$?

if [ "${replay}" -eq 0 ] && [ "${grade}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
