#!/bin/bash
# Two stages, and the reward is the product of both. The first runs what was submitted and is
# believed about nothing; the second grades as root and never executes a line of it.
set -euo pipefail

REWARD=/logs/verifier/reward.txt
SEAL=/tests/seal
BOX=/work
WHO=1002
CLOCK=60

verdict() {
  printf '%s\n' "$1" > "${REWARD}"
}

# Out of reach first, before anything the submission wrote has had a chance to run.
install -d -m 700 /logs/verifier
verdict 0
chmod 700 "${SEAL}"

# The seed is drawn here, with the agent's container already gone, so no submission has seen
# the plans it is about to be graded on. The grader reads these three from /logs/verifier; the
# worker is handed its own copies, which it is welcome to rewrite without shrinking its exam.
{
  python3 -c "import secrets; print(secrets.token_hex(16))" > /logs/verifier/nonce
  printf '40\n' > /logs/verifier/per
  printf '3\n' > /logs/verifier/scale
}
install -d -m 755 -o "${WHO}" -g "${WHO}" "${BOX}"
for part in nonce per scale; do
  install -m 644 -o "${WHO}" -g "${WHO}" "/logs/verifier/${part}" "${BOX}/${part}"
done

worker=0
setpriv --reuid="${WHO}" --regid="${WHO}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --out "${BOX}/worker_out.json" || worker=$?
printf 'worker exit %s\n' "${worker}"

python3 /tests/reap.py || true

grader=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf /logs/verifier/ctrf.json || grader=$?

if [ "${worker}" -eq 0 ] && [ "${grader}" -eq 0 ]; then
  verdict 1
else
  verdict 0
fi
