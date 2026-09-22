#!/bin/bash
# Grading, in two stages that trust each other in one direction only.
#
#   stage one   /tests/worker.py runs the submitted executor as an unprivileged user under the
#               wall clock that is also the task's execution limit, and records what every
#               graded program printed. It decides nothing.
#   stage two   /tests/test_outputs.py runs as root, never executes submitted code, and reads
#               stage one's record as hostile input against the sealed model.
#
# The reward is 0 from the first line and becomes 1 only when both stages exit cleanly.
set -euo pipefail

RUNNER=2201
VERDICT=/logs/verifier
SCRATCH=/scratch
CLOCK=60
EACH=36

# The reward directory and the sealed model belong to root and are closed before any submitted
# line runs, so nothing that outlives stage one can write a reward or read an answer.
install -d -m 700 "${VERDICT}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The population is drawn here, after the agent's container is gone. Stage two keeps its own
# copy of the seed in the root-only directory; stage one gets a copy it may damage without
# changing what it is graded on.
python3 -c 'import secrets; print(secrets.token_hex(16))' > "${VERDICT}/seed"
printf '%s\n' "${EACH}" > "${VERDICT}/each"
install -d -m 755 -o "${RUNNER}" -g "${RUNNER}" "${SCRATCH}"
install -m 644 -o "${RUNNER}" -g "${RUNNER}" "${VERDICT}/seed" "${VERDICT}/each" "${SCRATCH}/"

stage_one=0
setpriv --reuid="${RUNNER}" --regid="${RUNNER}" --clear-groups \
    timeout --kill-after=5 "${CLOCK}" \
    python3 /tests/worker.py "${SCRATCH}/record.json" || stage_one=$?
echo "stage one exited ${stage_one}"

python3 /tests/reap.py || true

stage_two=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${VERDICT}/ctrf.json" || stage_two=$?

if [ "${stage_one}" -eq 0 ] && [ "${stage_two}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
