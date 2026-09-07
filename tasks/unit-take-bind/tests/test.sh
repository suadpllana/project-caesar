#!/bin/bash
set -euo pipefail

# The reward channel is locked and defaulted to 0 before anything the submission wrote is
# staged, let alone executed, so nothing a survivor does later can reach it.
mkdir -p /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

python3 -c "import secrets; print(secrets.token_hex(16))" > /logs/verifier/nonce
echo 100 > /logs/verifier/per

# Everything the sandbox uid needs is staged here, as root, while /tests is still readable.
mkdir -p /work
cd /tests
python3 /tests/spread.py --out /work/progs.json \
    --nonce "$(cat /logs/verifier/nonce)" --per "$(cat /logs/verifier/per)"
cp -r /tests/pristine /work/tree
cp /tests/worker.py /work/worker.py
chown -R sandbox:sandbox /work

# From here the answers are root-only: the model, the frozen answers and the generator are
# behind a mode the sandbox uid cannot open.
chmod 700 /tests

set +e
setpriv --reuid=1002 --regid=1002 --clear-groups \
    timeout 600 setsid --wait python3 /work/worker.py --out /work/worker_out.json
worker_status=$?
set -e
echo "worker exit ${worker_status}"

python3 /tests/reap.py || true

set +e
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf /logs/verifier/ctrf.json
graded=$?
set -e

if [ "${graded}" -eq 0 ] && [ "${worker_status}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
