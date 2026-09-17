#!/bin/bash
# The graded run has two stages. The first executes the submission and is trusted with nothing.
# The second grades, as root, and never runs a line of it. The reward is written last, by the
# second, and only when both came back clean.
set -euo pipefail

seal=/tests/seal
logs=/logs/verifier
yard=/work
who=1002
clock=60
per=40

# Close the doors before the submission runs: the reward channel is root-only and already reads
# 0, and the model and the frozen answers are unreadable to the uid that is about to run.
install -d -m 700 "${logs}"
echo 0 > /logs/verifier/reward.txt
chmod 700 "${seal}"

# Draw the exam now, after the agent's container is gone, so no submission can have seen the
# programs it is judged on. The grader keeps its copy under ${logs}; the submission is handed
# its own under ${yard}, which it may rewrite without shrinking what it is judged on.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${logs}/nonce"
echo "${per}" > "${logs}/per"
install -d -m 755 -o "${who}" -g "${who}" "${yard}"
install -m 644 -o "${who}" -g "${who}" "${logs}/nonce" "${yard}/nonce"
install -m 644 -o "${who}" -g "${who}" "${logs}/per" "${yard}/per"

# Stage one: unprivileged, in a session of its own, under the clock that is the task's own
# execution limit. A correct service that cannot finish inside it fails exactly like a wrong one.
worker=0
setpriv --reuid="${who}" --regid="${who}" --clear-groups \
    timeout "${clock}" setsid --wait \
    python3 /tests/worker.py --out "${yard}/worker_out.json" || worker=$?
echo "worker exit ${worker}"

# A double fork outlives the session and the clock. It does not outlive its uid.
python3 /tests/reap.py || true

# Stage two: root, reading the record as hostile input.
grader=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q --ctrf "${logs}/ctrf.json" \
    || grader=$?

if [ "${worker}" -eq 0 ] && [ "${grader}" -eq 0 ]; then
  echo 1 > "${logs}/reward.txt"
else
  echo 0 > "${logs}/reward.txt"
fi
