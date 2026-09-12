#!/bin/bash
# Two stages, and only both of them coming back clean raises the reward. The first runs what
# the agent wrote, as an unprivileged uid, and is trusted for nothing. The second grades, as
# root, and never executes a line of it.
set -euo pipefail

logs=/logs/verifier
work=/work
uid=1002
wall=60
per=40

# Lock everything the reward is derived from before the first stage exists. A background
# process the run leaves behind cannot write into a root-owned directory at mode 700, and the
# model and the frozen answers are not readable by the uid that runs the submitted service.
install -d -m 700 "${logs}"
chmod 700 /tests/seal
echo 0 > /logs/verifier/reward.txt

# The seed is drawn here, once the agent's container is gone, so no submission has seen the
# programs it is about to be graded on. The grader keeps its copy under ${logs}; the worker is
# given its own under ${work}, which it may rewrite without shrinking its own exam.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${logs}/nonce"
printf '%s\n' "${per}" > "${logs}/per"
install -d -m 755 -o "${uid}" -g "${uid}" "${work}"
install -m 644 -o "${uid}" -g "${uid}" "${logs}/nonce" "${work}/nonce"
install -m 644 -o "${uid}" -g "${uid}" "${logs}/per" "${work}/per"

ran=0
setpriv --reuid="${uid}" --regid="${uid}" --clear-groups \
    timeout "${wall}" setsid --wait \
    python3 /tests/worker.py --out "${work}/worker_out.json" || ran=$?
printf 'worker exit %s\n' "${ran}"

# A double fork outlives the session and the clock alike. The uid it runs under does not.
python3 /tests/reap.py || true

graded=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${logs}/ctrf.json" || graded=$?

if [ "${ran}" -eq 0 ] && [ "${graded}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
