#!/bin/bash
# Two stages. The first runs what the agent wrote and is trusted for nothing; the second
# grades, as root, and never runs a line of it. Only both coming back clean raises the reward.
set -euo pipefail

logs=/logs/verifier
work=/work
uid=1002
wall=60
per=45

# Everything the reward is derived from is put out of reach before the first stage starts.
install -d -m 700 "${logs}"
printf '0\n' > /logs/verifier/reward.txt
chmod 700 /tests/seal

# Fixed seed makes verdicts reproducible. Root defines the complete set.
# The worker receives a copy; changing it cannot shrink the grader population.
printf '%s\n' 'source-manifest-v1-20260913' > /logs/verifier/nonce
printf '%s\n' "${per}" > "${logs}/per"
install -d -m 755 -o "${uid}" -g "${uid}" "${work}"
install -m 644 -o "${uid}" -g "${uid}" "${logs}/nonce" "${work}/nonce"
install -m 644 -o "${uid}" -g "${uid}" "${logs}/per" "${work}/per"

ran=0
TIMEFORMAT='worker seconds %R user %U sys %S'
time setpriv --reuid="${uid}" --regid="${uid}" --clear-groups \
    timeout "${wall}" setsid --wait \
    python3 /tests/worker.py --out "${work}/worker_out.json" || ran=$?
printf 'worker exit %s\n' "${ran}"

# A double fork outlives both the session and the clock. Ownership does not.
reaped=0
python3 /tests/reap.py || reaped=$?

graded=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${logs}/ctrf.json" || graded=$?

if [ "$ran" -eq 0 ] && [ "$graded" -eq 0 ] && [ "$reaped" -eq 0 ]; then
  printf '1\n' > /logs/verifier/reward.txt
else
  printf '0\n' > /logs/verifier/reward.txt
fi
