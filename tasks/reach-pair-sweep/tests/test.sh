#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

python3 -c "import secrets; print(secrets.token_hex(16))" > /logs/verifier/nonce
echo 80 > /logs/verifier/per

mkdir -p /work
cp /logs/verifier/nonce /work/nonce
cp /logs/verifier/per /work/per
chown -R sandbox:sandbox /work

set +e
setpriv --reuid=1002 --regid=1002 --clear-groups \
    timeout 900 setsid --wait python3 /tests/worker.py --out /work/worker_out.json
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
