#!/bin/bash
# Order matters here and is the whole of the isolation: every channel the submitted allocator
# might reach is closed before it runs, the reward starts refused, and only the two stages that
# ran clean can raise it.
set -euo pipefail

LOGS=/logs/verifier
WORK=/work
SEAL=/tests/seal
UID_SANDBOX=1002
WALL=60
PER=40

# 1. Refuse first. The reward directory is root-only and holds a 0 before any agent code exists,
#    so a submission that manages to stop the run mid-way inherits a failure and not a pass.
install -d -m 700 "${LOGS}"
echo 0 > /logs/verifier/reward.txt

# 2. The answers and the model go out of reach of the uid the worker will run as. They are baked
#    into this image, never uploaded, so this is the only door.
chmod 700 "${SEAL}"

# 3. The examination is drawn now, after the agent's container is gone. The pair lives in the
#    root-only directory; the worker gets a copy it may read and cannot write back, so a
#    submission cannot shrink the population it is graded on.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${LOGS}/nonce"
echo "${PER}" > "${LOGS}/per"

install -d -m 755 -o "${UID_SANDBOX}" -g "${UID_SANDBOX}" "${WORK}"
install -m 444 -o "${UID_SANDBOX}" -g "${UID_SANDBOX}" "${LOGS}/nonce" "${WORK}/nonce"
install -m 444 -o "${UID_SANDBOX}" -g "${UID_SANDBOX}" "${LOGS}/per" "${WORK}/per"

# 4. The one stage that executes agent code. Unprivileged, in its own session, under the wall
#    clock that is also the task's execution limit.
worker=0
setpriv --reuid="${UID_SANDBOX}" --regid="${UID_SANDBOX}" --clear-groups \
    timeout "${WALL}" setsid --wait \
    python3 /tests/worker.py --out "${WORK}/worker_out.json" || worker=$?
echo "worker exit ${worker}"

# 5. Anything it left behind goes now, before the grader reads a line.
python3 /tests/reap.py || true

# 6. Grading, as root, over the record the worker left. It runs no agent code.
graded=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${LOGS}/ctrf.json" || graded=$?

# 7. Both stages have to have finished clean. A worker that crashed, hung or exited early is a
#    failure however the grader reads its leftovers.
if [ "${worker}" -eq 0 ] && [ "${graded}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
