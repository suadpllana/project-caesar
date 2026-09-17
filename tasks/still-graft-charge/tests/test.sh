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

# The seed is drawn now, after the agent's container is gone, so no submission has seen the
# programs it will be graded on. The grader reads the pair from ${logs}; the worker gets its
# own copy under ${work}, which it may rewrite without shrinking its own exam.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${logs}/nonce"
printf '%s\n' "${per}" > "${logs}/per"
install -d -m 755 -o "${uid}" -g "${uid}" "${work}"
install -m 644 -o "${uid}" -g "${uid}" "${logs}/nonce" "${work}/nonce"
install -m 644 -o "${uid}" -g "${uid}" "${logs}/per" "${work}/per"

ran=0
setpriv --reuid="${uid}" --regid="${uid}" --clear-groups \
    timeout "${wall}" setsid --wait \
    python3 /tests/worker.py --out "${work}/worker_out.json" || ran=$?
printf 'worker exit %s\n' "${ran}"

# A double fork outlives both the session and the clock. Ownership does not.
python3 /tests/reap.py || true

graded=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${logs}/ctrf.json" || graded=$?

if [ "${ran}" -eq 0 ] && [ "${graded}" -eq 0 ]; then
  printf '1\n' > /logs/verifier/reward.txt
else
  printf '0\n' > /logs/verifier/reward.txt
fi
