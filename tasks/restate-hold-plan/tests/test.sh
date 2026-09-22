#!/bin/bash
# The verifier's entry point. Two stages, and only the second decides anything.
#
#   stage one  uid 1002, a session of its own, the task's 60 second clock: the submitted
#              planner is laid over a pristine tree and run on every graded pipeline, and what
#              it printed lands in /work/planned.json. Trusted for nothing.
#   stage two  root, pytest: that file is read as hostile input and every plan is compared
#              with the frozen answers and the sealed model. Nothing submitted runs here.
#
# reward.txt reads 0 from the first moment and becomes 1 only after both stages exited 0.
set -euo pipefail

LOGS=/logs/verifier
WORK=/work
PLANNER_UID=1002
CLOCK=60
EACH=40

# The reward directory and the sealed side are locked before any submitted line runs: root
# owns both and 0700 keeps uid 1002 out, including anything it leaves running.
mkdir -p "${LOGS}"
chown root:root "${LOGS}"
chmod 700 "${LOGS}"
echo 0 > /logs/verifier/reward.txt
chown -R root:root /tests/seal
chmod 700 /tests/seal

# The generated population comes from a seed drawn here, after the agent's container is gone.
# Stage two keeps its own copy under the locked directory; stage one gets one it may overwrite
# without changing the set it is graded on.
python3 -c 'import secrets; print(secrets.token_hex(16))' > "${LOGS}/seed"
printf '%s\n' "${EACH}" > "${LOGS}/each"
rm -rf "${WORK}"
mkdir -p "${WORK}"
cp "${LOGS}/seed" "${LOGS}/each" "${WORK}/"
chown -R "${PLANNER_UID}:${PLANNER_UID}" "${WORK}"

stage_one=0
setpriv --reuid="${PLANNER_UID}" --regid="${PLANNER_UID}" --clear-groups \
    timeout -k 5 "${CLOCK}" setsid --wait \
    python3 /tests/worker.py "${WORK}/planned.json" || stage_one=$?
echo "stage one exited ${stage_one}"

python3 /tests/reap.py || true

stage_two=0
python3 -m pytest /tests/test_outputs.py -q -p no:cacheprovider \
    --ctrf "${LOGS}/ctrf.json" || stage_two=$?
echo "stage two exited ${stage_two}"

if [ "${stage_one}" -eq 0 ] && [ "${stage_two}" -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
