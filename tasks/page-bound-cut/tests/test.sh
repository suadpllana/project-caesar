#!/bin/bash
# Two stages, and only one of them ever touches submitted code.
#
#   stage one   lays the five submitted files over a pristine tree, runs every graded
#               program and writes down what each one printed. It runs as an unprivileged
#               user, inside its own session, under a wall clock, and it decides nothing.
#   stage two   runs as root, executes nothing that was submitted, and reads stage one's
#               file as hostile input.
#
# The reward is 0 until both stages have come back clean.
set -euo pipefail

PEN=1002
VERDICT=/logs/verifier
YARD=/work
CLOCK=120
EACH=8

# The reward channel and the sealed answers are shut before a submitted line runs. Root owns
# both, and 0700 keeps the pen user out of them even if something it started outlives the call.
install -d -m 700 /logs/verifier
printf '0\n' > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn now, with the agent's container already gone, so nothing that was
# submitted has seen the programs it is about to be graded on. Stage two keeps the
# authoritative copy under the root-only directory; stage one is handed its own, which it may
# rewrite without shrinking the set it is actually marked against.
python3 -c "import secrets, sys; sys.stdout.write(secrets.token_hex(16))" > "${VERDICT}/seed"
printf '%s' "${EACH}" > "${VERDICT}/each"
install -d -m 755 -o "${PEN}" -g "${PEN}" "${YARD}"
install -m 444 -o root -g root "${VERDICT}/seed" "${VERDICT}/each" "${YARD}/"

stage_one=0
setpriv --reuid="${PEN}" --regid="${PEN}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --into "${YARD}/traces.json" || stage_one=$?
printf 'stage one exited %s\n' "${stage_one}"

python3 /tests/reap.py || true

stage_two=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${VERDICT}/ctrf.json" || stage_two=$?

if [ "${stage_one}" -eq 0 ] && [ "${stage_two}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
