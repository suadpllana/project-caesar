#!/bin/bash
# Verifier entry point for journal-gap-mend.
#
# Two stages. The first runs the submitted recovery tool as uid 1002, in a session of its
# own, under the 120 s clock the brief states, and only records what it printed. The second
# runs as root, executes nothing that was submitted, and grades those records against
# printouts it worked out before the first stage started. Reward 1 needs both clean.
set -euo pipefail

SANDBOX=1002
VERDICT=/logs/verifier
SCRATCH=/work
CLOCK=120
PER_FAMILY=30

# Before any submitted code exists as a process: the verdict directory turns root-only and
# holds a 0, and the sealed model, generator and frozen answers go dark to uid 1002.
install -d -m 0700 "${VERDICT}"
echo 0 > /logs/verifier/reward.txt
chmod 0700 /tests/seal

# A fresh seed, drawn after the agent's container is gone. The graded set and its expected
# printouts are built now, into the root-only directory; the worker receives journal texts.
python3 -c 'import secrets; print(secrets.token_hex(16))' > "${VERDICT}/nonce"
python3 /tests/seal/prep.py --seed-file "${VERDICT}/nonce" --per "${PER_FAMILY}" \
    --out "${VERDICT}/set.json" --texts "${VERDICT}/journals.json"
install -d -m 0755 -o "${SANDBOX}" -g "${SANDBOX}" "${SCRATCH}"
install -m 0644 -o "${SANDBOX}" -g "${SANDBOX}" "${VERDICT}/journals.json" "${SCRATCH}/journals.json"

run_status=0
setpriv --reuid="${SANDBOX}" --regid="${SANDBOX}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --out "${SCRATCH}/worker_out.json" || run_status=$?
echo "half one exited ${run_status}"

# Whatever the run left alive is killed by owner before a line of its output is graded.
python3 /tests/reap.py || true

grade_status=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q -rfE \
    --ctrf "${VERDICT}/ctrf.json" || grade_status=$?

if (( run_status == 0 && grade_status == 0 )); then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
