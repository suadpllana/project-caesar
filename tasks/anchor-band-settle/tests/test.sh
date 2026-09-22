#!/bin/bash
# Two halves that trust each other one way only.
#
#   half one   executes the submitted view modules, unprivileged, and writes down what each
#              graded program printed. It reaches no verdict.
#   half two   runs as root, executes not one submitted line, and reads half one's file as
#              input from an adversary.
#
# The reward begins at 0 and is lifted only when both halves returned clean.
set -euo pipefail

SBOX_UID=1002
VDIR=/logs/verifier          # root-only: the reward, the nonce, the exam's hash
EXAM=/tests/run              # world-readable: the programs half one is graded on
WORK=/work                  # owned by the sandbox: half one's scratch and its output
WALL=90                     # the whole of half one must finish inside this many seconds
PER=30                      # generated programs per small family

# Seal the verdict channel and the answers before a single submitted line runs. Root owns
# both and 0700 keeps uid 1002 out even if a process outlives the call.
install -d -m 700 "${VDIR}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# Draw the seed now, with the agent's container already gone, so nothing submitted has seen the
# programs it faces. Root writes them where the sandbox may read but not write, and keeps their
# hash where only root can read it, so half two can prove it graded the file half one was given.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${VDIR}/nonce"
install -d -m 755 "${EXAM}"
python3 /tests/gen.py --seed "$(cat "${VDIR}/nonce")" --per "${PER}" \
    --out "${EXAM}/progs.json"
chmod 644 "${EXAM}/progs.json"
sha256sum "${EXAM}/progs.json" | cut -d' ' -f1 > "${VDIR}/progs.sha"
install -d -m 755 -o "${SBOX_UID}" -g "${SBOX_UID}" "${WORK}"

half_one=0
setpriv --reuid="${SBOX_UID}" --regid="${SBOX_UID}" --clear-groups \
    timeout "${WALL}" setsid --wait \
    python3 /tests/worker.py --progs "${EXAM}/progs.json" \
    --out "${WORK}/worker_out.json" || half_one=$?
printf 'half one exited %s\n' "${half_one}"

python3 /tests/reap.py || true

half_two=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${VDIR}/ctrf.json" || half_two=$?

if [ "${half_one}" -eq 0 ] && [ "${half_two}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
