#!/bin/bash
set -euo pipefail

# The reward channel is locked and defaulted before anything else happens, so a
# process the submitted trainer leaves behind has nowhere to write a verdict.
mkdir -p /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt

# The nonce stays on the root-only side. The scripts it selects are handed to the
# worker; the expected traces are not, and neither is the seed they came from.
python3 -c "import secrets; print(secrets.token_hex(16))" > /logs/verifier/nonce
echo 55 > /logs/verifier/per

mkdir -p /work
python3 /tests/seal/plan.py --out /work/scripts.json --logs /logs/verifier
test -s /work/scripts.json
chown -R sandbox:sandbox /work

# The only stage that runs agent code: unprivileged, in its own session, time-bounded.
set +e
setpriv --reuid=1002 --regid=1002 --clear-groups \
    timeout 300 setsid --wait python3 /tests/worker.py \
    --scripts /work/scripts.json --out /work/worker_out.json
ran=$?
set -e
echo "worker exit ${ran}"

python3 /tests/reap.py || true

set +e
python3 -m pytest /tests/seal/test_outputs.py -p no:cacheprovider -q \
    --ctrf /logs/verifier/ctrf.json
verdict=$?
set -e

if [ "${ran}" -eq 0 ] && [ "${verdict}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
