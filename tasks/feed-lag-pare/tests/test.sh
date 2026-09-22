#!/bin/bash
# Two stages, trusting each other in one direction. The first runs the submitted retention
# half as an unprivileged user and only writes down what each graded program printed; the
# second grades as root and never executes a line of it. The reward starts at 0 and is raised
# only when both came back clean.
set -euo pipefail

logs=/logs/verifier
work=/work
uid=1002
wall=60
per=40

# Everything the reward is derived from goes out of reach before the first stage starts:
# root owns the reward directory at 0700, and the model and the frozen answers with it.
install -d -m 700 "${logs}"
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The seed is drawn now, with the agent's container already gone, so nothing that was
# submitted has seen the programs it is about to be graded on. The authoritative copy stays
# in the root-owned directory; the first stage gets its own, which it may rewrite as much as
# it likes without shrinking the exam it is actually marked against.
python3 -c "import secrets; print(secrets.token_hex(16))" > "${logs}/nonce"
printf '%s\n' "${per}" > "${logs}/per"
install -d -m 755 -o "${uid}" -g "${uid}" "${work}"
install -m 644 -o "${uid}" -g "${uid}" "${logs}/nonce" "${logs}/per" "${work}/"

first=0
setpriv --reuid="${uid}" --regid="${uid}" --clear-groups \
    timeout "${wall}" setsid --wait \
    python3 /tests/worker.py --out "${work}/worker_out.json" || first=$?
printf 'stage one exited %s\n' "${first}"

# A double fork walks out of both the session and the clock, so the survivors are swept by
# owner before the grader reads anything.
python3 /tests/reap.py || true

second=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf "${logs}/ctrf.json" || second=$?

if [ "${first}" -eq 0 ] && [ "${second}" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
