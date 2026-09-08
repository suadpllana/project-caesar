#!/bin/bash
# The verifier, in five stages: lock the reward channel, draw the nonce, build the graded
# scripts as root and seal everything that knows the answers, run the submitted layer as an
# unprivileged uid, then grade it as root. Nothing between stages trusts the one before it -
# the reward is written last, from the grader's exit status and the worker's.
set -euo pipefail

readonly LOGS=/logs/verifier
readonly WORK=/work
readonly FEED=/feed
readonly SANDBOX=1002
readonly BUDGET=60

mkdir -p "${LOGS}"
chmod 700 "${LOGS}"
echo 0 > /logs/verifier/reward.txt

python3 -c "import secrets; print(secrets.token_hex(16))" > "${LOGS}/nonce"
echo 70 > "${LOGS}/per"

mkdir -p "${FEED}"
python3 /tests/prep.py --out "${FEED}/scripts.json"
chown -R root:root "${FEED}"
chmod 555 "${FEED}"
chmod 444 "${FEED}/scripts.json"

# Everything that can answer a script, or reproduce the population, is root-only from here on.
chmod 600 /tests/model.py /tests/gt.json /tests/cases.py /tests/gen.py \
          /tests/prep.py /tests/test_outputs.py

mkdir -p "${WORK}"
chown "${SANDBOX}:${SANDBOX}" "${WORK}"

worker=0
setpriv --reuid="${SANDBOX}" --regid="${SANDBOX}" --clear-groups \
    timeout "${BUDGET}" setsid --wait \
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
