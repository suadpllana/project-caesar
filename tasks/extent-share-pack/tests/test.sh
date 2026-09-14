#!/bin/bash
# The graded run has two halves. The first executes what was submitted and is believed about
# nothing; the second grades it as root and executes none of it. The reward moves off 0 only when
# both halves come back clean.
set -euo pipefail

VERDICT=/logs/verifier
SPACE=/work
LOW=1002
CLOCK=60
EACH=45

lock() {
  # Done before the first line of submitted code runs: the reward file exists, says 0, and sits
  # in a directory only root may enter, and the answers lose their group and other bits.
  install -d -m 700 "${VERDICT}"
  echo 0 > /logs/verifier/reward.txt
  chmod 700 /tests/seal
}

exam() {
  # Drawn here, with the agent's container already torn down, so nothing that ran there has seen
  # the programs it is about to be graded on. The grader keeps its pair in ${VERDICT}; the
  # unprivileged half gets a copy it is free to vandalise without shrinking its own exam.
  python3 -c "import secrets; print(secrets.token_hex(16))" > "${VERDICT}/nonce"
  printf '%s\n' "${EACH}" > "${VERDICT}/per"
  install -d -m 755 -o "${LOW}" -g "${LOW}" "${SPACE}"
  install -m 644 -o "${LOW}" -g "${LOW}" "${VERDICT}/nonce" "${SPACE}/nonce"
  install -m 644 -o "${LOW}" -g "${LOW}" "${VERDICT}/per" "${SPACE}/per"
}

lock
exam

first=0
setpriv --reuid="${LOW}" --regid="${LOW}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --out "${SPACE}/worker_out.json" || first=$?
printf 'submitted half exited %s\n' "${first}"

# A double fork leaves both the session and the clock behind it. It does not leave the uid.
python3 /tests/reap.py || true

second=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${VERDICT}/ctrf.json" || second=$?

if [ "${first}" -eq 0 ] && [ "${second}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
