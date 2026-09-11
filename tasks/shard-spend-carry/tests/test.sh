#!/bin/bash
# The verifier runs in two halves. The first executes what the agent wrote and is believed
# about nothing; the second grades as root and never imports a line of it. The reward starts
# at 0, and only both halves coming back clean raises it.
set -euo pipefail

LOGS=/logs/verifier
WORK=/work
SANDBOX=1002
WALL=120
PER=45

# Lock the reward channel and seal the answers before anything the agent wrote can run.
install -d -m 700 "$LOGS"
printf '0\n' > /logs/verifier/reward.txt
chmod 700 /tests/seal

# Draw the seed now. The agent's container is already gone, so no submission has seen the
# programs it is about to be graded on. The grader keeps its copy inside the root-only
# directory; the worker gets its own under $WORK and is welcome to rewrite that one.
python3 -c 'import secrets; print(secrets.token_hex(16))' > "$LOGS/nonce"
printf '%s\n' "$PER" > "$LOGS/per"
install -d -m 755 -o "$SANDBOX" -g "$SANDBOX" "$WORK"
install -m 644 -o "$SANDBOX" -g "$SANDBOX" "$LOGS/nonce" "$WORK/nonce"
install -m 644 -o "$SANDBOX" -g "$SANDBOX" "$LOGS/per" "$WORK/per"

worker=0
setpriv --reuid="$SANDBOX" --regid="$SANDBOX" --clear-groups \
    timeout "$WALL" setsid --wait \
    python3 /tests/worker.py --out "$WORK/worker_out.json" || worker=$?
echo "worker stage exit $worker"

# A double fork walks out of both the session and the clock. It does not change owner.
python3 /tests/reap.py || true

grader=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "$LOGS/ctrf.json" || grader=$?
echo "grading stage exit $grader"

if [ "$worker" -eq 0 ] && [ "$grader" -eq 0 ]; then
  printf '1\n' > /logs/verifier/reward.txt
else
  printf '0\n' > /logs/verifier/reward.txt
fi
