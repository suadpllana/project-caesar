#!/bin/bash
# The verifier in two stages, and only the second one is trusted.
#
# Stage one runs the submitted panel. It is unprivileged, it is in a session of its own, it is
# under the wall clock that is also the task's execution limit, and its only product is a
# record of what each program printed. Stage two grades that record as root and never runs a
# line of the submission. The reward starts at 0 and is raised only when both stages came back
# clean, by this script, last.
set -euo pipefail

LOGS=/logs/verifier
WORK=/work
SAND=1002
CLOCK=60
PER=40

arm() {
  # The reward channel is closed before anything the agent wrote has run, so a process that
  # outlives grading has nowhere to write its verdict. The sealed answers and the independent
  # model go out of reach of the sandbox uid at the same time.
  install -d -m 700 "${LOGS}"
  printf '0\n' > /logs/verifier/reward.txt
  chmod 700 /tests/seal
}

draw() {
  # The seed is drawn now, with the agent's container already gone, so no submission has seen
  # the programs it is about to be graded on. The grader keeps its copy in ${LOGS}; the worker
  # gets its own under ${WORK} and may rewrite that one without shrinking its own exam.
  python3 -c "import secrets; print(secrets.token_hex(16))" > "${LOGS}/nonce"
  printf '%s\n' "${PER}" > "${LOGS}/per"
  install -d -m 755 -o "${SAND}" -g "${SAND}" "${WORK}"
  install -m 644 -o "${SAND}" -g "${SAND}" "${LOGS}/nonce" "${WORK}/nonce"
  install -m 644 -o "${SAND}" -g "${SAND}" "${LOGS}/per" "${WORK}/per"
}

arm
draw

ran=0
setpriv --reuid="${SAND}" --regid="${SAND}" --clear-groups \
    timeout "${CLOCK}" setsid --wait \
    python3 /tests/worker.py --out "${WORK}/worker_out.json" || ran=$?
printf 'worker exit %s\n' "${ran}"

# A double fork walks out of both the session and the clock. It cannot walk out of its uid.
python3 /tests/reap.py || true

graded=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${LOGS}/ctrf.json" || graded=$?

if [ "${ran}" -eq 0 ] && [ "${graded}" -eq 0 ]; then
  printf '1\n' > "${LOGS}/reward.txt"
else
  printf '0\n' > /logs/verifier/reward.txt
fi
