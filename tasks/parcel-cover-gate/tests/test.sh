#!/bin/bash
# Verifier entry point.
#
# The shape of this file follows from one requirement: the reward, and every
# input the reward is worked out from, has to sit where executed agent code
# cannot write. Everything below is that requirement applied step by step.
#
# The reward channel is closed and defaulted to refuse before any submitted line
# is loaded. The tree that runs is built root-owned and read-only out of an
# untouched copy, with the four declared files laid over it and nothing else, so
# an edit outside them is impossible rather than merely caught afterwards. The
# report file belongs to root and reaches the run as an inherited descriptor,
# after the drop, so the uid that executes agent code does not own the file it is
# graded on. The run is given its own session and a wall clock, and anything that
# outlives it is reaped before a row is read. Grading runs afterwards as root,
# under pytest, and executes nothing the agent wrote.
#
# The nonce is drawn at the top of the run, after the agent has finished, and it
# seeds the three hundred feeds this submission is really graded on. Both sides
# are given the same nonce, so the run and the grader are talking about the same
# feeds without either of them having had those feeds earlier.
set -Eeuo pipefail

WORK=/work
PURE=/pristine
LOGS=/logs/verifier
OPEN="bay/desc.py bay/cov.py bay/stand.py bay/gate.py"

close_the_channel() {
  mkdir -p "${LOGS}"
  chown root:root "${LOGS}"
  chmod 700 "${LOGS}"
  echo 0 > /logs/verifier/reward.txt
  chown root:root /tests/gt.json /tests/oracle.py /tests/test_outputs.py
  chmod 600 /tests/gt.json /tests/oracle.py /tests/test_outputs.py
}

lay_the_tree() {
  rm -rf "${WORK}"
  mkdir -p "${WORK}/app" "${WORK}/run"
  cp -a "${PURE}/." "${WORK}/app/"
  for rel in ${OPEN}; do
    [ -f "/app/${rel}" ] && cp -f "/app/${rel}" "${WORK}/app/${rel}"
  done
  find "${WORK}/app" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
  find "${WORK}/app" -name '*.pyc' -delete 2>/dev/null || true
  chown -R root:root "${WORK}"
  chmod -R u=rwX,go=rX "${WORK}/app"
  chmod 755 "${WORK}" "${WORK}/run"
  install -d -o sandbox -g sandbox -m 700 "${WORK}/scratch"
  : > "${WORK}/run/out.json"
  chown root:root "${WORK}/run/out.json"
  chmod 600 "${WORK}/run/out.json"
}

close_the_channel
lay_the_tree

RUN_NONCE="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
RUN_COUNT=300
export RUN_NONCE RUN_COUNT

set +e
exec 9>"${WORK}/run/out.json"
setsid --wait env APPDIR="${WORK}/app" TMPDIR="${WORK}/scratch" HOME="${WORK}/scratch" \
    PYTHONDONTWRITEBYTECODE=1 RUN_NONCE="${RUN_NONCE}" RUN_COUNT="${RUN_COUNT}" \
  setpriv --reuid=1002 --regid=1002 --clear-groups \
  timeout --signal=KILL 900 python /tests/runner.py "fd:9"
exec 9>&-
python /tests/reap.py 1002
set -e

if RUN_OUT="${WORK}/run/out.json" APP_DIR="${WORK}/app" PRISTINE_DIR="${PURE}" \
   pytest --ctrf "${LOGS}/ctrf.json" /tests/test_outputs.py -rA; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
