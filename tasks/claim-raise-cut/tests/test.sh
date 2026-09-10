#!/bin/bash
set -euo pipefail

LOGS=/logs/verifier
WORK=/work
SANDBOX=1002
LIMIT=60
PER=40
HEAVY=6

# The reward channel and the sealed answers are shut before anything the agent wrote runs, and
# the reward starts at 0: only a worker that returned cleanly and a grader that passed raise it.
install -d -m 700 "${LOGS}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

python3 -c "import secrets; print(secrets.token_hex(16))" > "${LOGS}/nonce"
echo "${PER}" > "${LOGS}/per"
echo "${HEAVY}" > "${LOGS}/heavy"

# The worker is handed its own copy of the seed and the two population sizes. The grader reads
# the originals from ${LOGS}, which the worker's uid cannot write, so a submission cannot cut
# its own exam down.
install -d -m 755 -o "${SANDBOX}" -g "${SANDBOX}" "${WORK}"
cp "${LOGS}/nonce" "${LOGS}/per" "${LOGS}/heavy" "${WORK}/"
chown "${SANDBOX}:${SANDBOX}" "${WORK}/nonce" "${WORK}/per" "${WORK}/heavy"

worker=0
setpriv --reuid="${SANDBOX}" --regid="${SANDBOX}" --clear-groups \
    timeout "${LIMIT}" setsid --wait \
    python3 /tests/worker.py --out "${WORK}/worker_out.json" || worker=$?
echo "worker exit ${worker}"

python3 /tests/reap.py || true

graded=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${LOGS}/ctrf.json" || graded=$?

if [ "${worker}" -eq 0 ] && [ "${graded}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
