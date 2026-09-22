#!/bin/bash
set -euo pipefail

LOGS=/logs/verifier
WORK=/work
SANDBOX=1002
LIMIT=180
PER=30

# The reward channel and the sealed answers are locked before anything the agent wrote runs,
# and the reward starts at 0: only a clean worker and a clean grader can raise it.
install -d -m 700 "${LOGS}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

python3 -c "import secrets; print(secrets.token_hex(16))" > "${LOGS}/nonce"
echo "${PER}" > "${LOGS}/per"

# The graded scripts are written by root from the nonce before the worker starts, and their
# answers go into the sealed directory. The worker can read the scripts and nothing else of it.
install -d -m 755 "${WORK}"
install -d -m 755 "${WORK}/scripts"
python3 /tests/seal/make.py --seed-file "${LOGS}/nonce" --per "${PER}" \
    --scripts "${WORK}/scripts" --answers /tests/seal/expected.json

# The tree the scripts run in is staged by root: the verifier's pristine copy with the five
# submitted files laid over it, root-owned and read-only, so nothing a script runs can change
# the driver, the reader, the store or the printer that the next script runs under.
cp -r /tests/pristine "${WORK}/tree"
for part in match drop clear hold audit; do
  if [ -f "/app/db/${part}.py" ]; then
    cp "/app/db/${part}.py" "${WORK}/tree/db/${part}.py"
  fi
done
chown -R root:root "${WORK}/tree"
chmod -R a-w,a+rX "${WORK}/tree"
install -d -m 755 -o "${SANDBOX}" -g "${SANDBOX}" "${WORK}/run"

worker=0
start=${SECONDS}
setpriv --reuid="${SANDBOX}" --regid="${SANDBOX}" --clear-groups \
    timeout "${LIMIT}" setsid --wait \
    python3 /tests/worker.py --tree "${WORK}/tree" --out "${WORK}/run/worker_out.jsonl" || worker=$?
echo "worker exit ${worker} after $((SECONDS - start)) s"

python3 /tests/reap.py || true

graded=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${LOGS}/ctrf.json" || graded=$?

if [ "${worker}" -eq 0 ] && [ "${graded}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
