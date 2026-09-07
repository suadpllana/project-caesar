#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

python3 -c "import secrets; print(secrets.token_hex(16))" > /logs/verifier/nonce
echo 60 > /logs/verifier/per

mkdir -p /work
python3 /tests/prepare.py \
    --nonce-file /logs/verifier/nonce \
    --per-file /logs/verifier/per \
    --out /work/programs.json \
    --tree /work/pristine
cp /tests/worker.py /work/worker.py
chown -R sandbox:sandbox /work
chmod -R go-rwx /tests

set +e
setpriv --reuid=1002 --regid=1002 --clear-groups \
    timeout 60 setsid --wait env -u PYTHONPATH -u PYTHONHOME -u RPS_TESTS -u RPS_LOGS \
    python3 /work/worker.py --out /work/worker_out.json
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
