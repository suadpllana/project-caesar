#!/bin/bash
# Two stages, trusted in one direction only.
#
#   worker   runs the submitted evaluator as an unprivileged user and records what every
#            graded program printed. It decides nothing.
#   grader   runs as root, never executes submitted code, recomputes every expected report
#            and treats the worker's record as hostile.
#
# reward.txt holds 0 from the first line of this script and becomes 1 only when both stages
# exit cleanly. It lives in a root-owned 0700 directory locked before any submitted code runs.
set -euo pipefail

SANDBOX=1002
VERDICT=/logs/verifier
SCRATCH=/work
LIMIT_SECONDS=90
PER_FAMILY=30

install -d -m 700 "${VERDICT}"
echo 0 > "${VERDICT}/reward.txt"
chmod 700 /tests/seal

# The programs are generated from a seed drawn now, after the agent's container is gone. The
# grader keeps its copy in the locked directory; the worker gets its own, which it may alter
# without changing the programs it is graded on.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${VERDICT}/nonce"
echo "${PER_FAMILY}" > "${VERDICT}/per"
install -d -m 755 -o "${SANDBOX}" -g "${SANDBOX}" "${SCRATCH}"
install -m 644 -o "${SANDBOX}" -g "${SANDBOX}" "${VERDICT}/nonce" "${SCRATCH}/seed"
install -m 644 -o "${SANDBOX}" -g "${SANDBOX}" "${VERDICT}/per" "${SCRATCH}/per"

worker=0
setpriv --reuid="${SANDBOX}" --regid="${SANDBOX}" --clear-groups \
    timeout "${LIMIT_SECONDS}" setsid --wait \
    python3 /tests/worker.py --out "${SCRATCH}/runs.json" || worker=$?
echo "worker exit status: ${worker}"

python3 /tests/reap.py || true

grader=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${VERDICT}/ctrf.json" || grader=$?

if [ "${worker}" -eq 0 ] && [ "${grader}" -eq 0 ]; then
  echo 1 > "${VERDICT}/reward.txt"
else
  echo 0 > "${VERDICT}/reward.txt"
fi
