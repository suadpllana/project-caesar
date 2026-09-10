#!/bin/bash
set -euo pipefail

LOGS=/logs/verifier
WORK=/work
SANDBOX=1002
LIMIT=120
PER=75

# The reward channel and the sealed answers are locked before anything the agent wrote runs, and
# the reward starts at 0: only a clean worker and a clean grader can raise it.
install -d -m 700 "${LOGS}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

python3 -c "import secrets; print(secrets.token_hex(16))" > "${LOGS}/nonce"
echo "${PER}" > "${LOGS}/per"

# The worker gets its own copy of the seed and the family size. The grader reads the pair in
# ${LOGS}, which the worker's uid cannot write, so a submission cannot shrink its own exam.
install -d -m 755 -o "${SANDBOX}" -g "${SANDBOX}" "${WORK}"
cp "${LOGS}/nonce" "${LOGS}/per" "${WORK}/"
chown "${SANDBOX}:${SANDBOX}" "${WORK}/nonce" "${WORK}/per"

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
