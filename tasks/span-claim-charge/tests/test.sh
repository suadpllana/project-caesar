#!/bin/bash
# Root stage. Nothing the agent wrote runs here; it runs in the worker, one uid down.
set -euo pipefail

logs=/logs/verifier
work=/work
uid=1002
wall=60
per=45

# Order matters. The reward channel and the sealed answers are shut before a line of the
# submitted store runs, and the reward starts at 0, so only a clean worker followed by a
# clean grader can raise it.
install -d -m 700 "${logs}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

python3 -c 'import secrets; print(secrets.token_hex(16))' > "${logs}/nonce"
echo "${per}" > "${logs}/per"

# The worker is handed its own copy of the seed and the family size. The grader reads the
# pair from ${logs}, which the worker's uid cannot write, so a submission that rewrites
# what it was handed shrinks nothing.
install -d -m 755 -o "${uid}" -g "${uid}" "${work}"
install -m 644 -o "${uid}" -g "${uid}" "${logs}/nonce" "${work}/nonce"
install -m 644 -o "${uid}" -g "${uid}" "${logs}/per" "${work}/per"

ran=0
setpriv --reuid="${uid}" --regid="${uid}" --clear-groups \
    timeout "${wall}" setsid --wait \
    python3 /tests/worker.py --out "${work}/worker_out.json" || ran=$?
echo "worker exit ${ran}"

python3 /tests/reap.py || true

judged=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${logs}/ctrf.json" || judged=$?
echo "grader exit ${judged}"

if [ "${ran}" -eq 0 ] && [ "${judged}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
