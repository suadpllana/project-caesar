#!/bin/bash
# Grading runs in two stages with a hard line between them. Stage one replays the graded
# programs under the submitted driver; it is unprivileged and is trusted for nothing. Stage two
# is the grader, runs as root, and never executes a line of what the agent wrote. The reward is
# written last, by this script, and only when both stages came back clean.
set -euo pipefail

LOGS=/logs/verifier
WORK=/work
SEAL=/tests/seal
SANDBOX=1002
EXEC_LIMIT=120      # also the task's stated execution limit
PER_FAMILY=45      # generated programs per small family; the brief's counts derive from this

fail() {
    printf '0\n' > /logs/verifier/reward.txt
    printf 'verdict 0: %s\n' "$1"
    exit 0
}

# Everything the reward is derived from goes out of reach before stage one starts. The reward
# file exists and reads 0 from here on; only the last line of this script can change that.
install -d -m 700 "${LOGS}"
printf '0\n' > /logs/verifier/reward.txt
chmod 700 "${SEAL}"

# The seed is drawn now, with the agent's container already gone, so no submission has seen the
# programs it is about to be graded on. The grader reads the pair from ${LOGS}, which the
# sandbox uid cannot reach; stage one gets its own copy under ${WORK} and may rewrite that copy
# as much as it likes without shrinking its own exam.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${LOGS}/nonce"
printf '%s\n' "${PER_FAMILY}" > "${LOGS}/per"
install -d -m 755 -o "${SANDBOX}" -g "${SANDBOX}" "${WORK}"
install -m 644 -o "${SANDBOX}" -g "${SANDBOX}" "${LOGS}/nonce" "${WORK}/nonce"
install -m 644 -o "${SANDBOX}" -g "${SANDBOX}" "${LOGS}/per" "${WORK}/per"

record="${WORK}/worker_out.json"
worker=0
setpriv --reuid="${SANDBOX}" --regid="${SANDBOX}" --clear-groups \
    timeout "${EXEC_LIMIT}" setsid --wait \
    python3 /tests/worker.py --out "${record}" || worker=$?
printf 'stage one exit %s\n' "${worker}"

# A double fork walks out of both the session and the clock. The uid it had to run under does
# not, and nothing else in this container holds that uid.
python3 /tests/reap.py || true

[ "${worker}" -eq 0 ] || fail "the submitted driver did not finish inside ${EXEC_LIMIT}s"
[ -s "${record}" ] || fail "the submitted driver left no record"

grader=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${LOGS}/ctrf.json" || grader=$?
[ "${grader}" -eq 0 ] || fail "the graded traces do not match"

printf '1\n' > /logs/verifier/reward.txt
printf 'verdict 1\n'
