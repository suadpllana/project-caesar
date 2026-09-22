#!/bin/bash
# Two stages, and only the second one decides anything.
#
#   run     the six submitted files execute, as uid 1002 in a session of their own, under the
#           task's 60 second clock; what they leave in /work is evidence, never a verdict
#   judge   pytest as root: it imports no submitted code and parses /work as untrusted input
#
# reward.txt reads 0 from the first line on, and is set to 1 only when both stages exit 0.
set -euo pipefail

# Every root interpreter below runs isolated (-I) from a directory the submission cannot write, so
# no file it left behind can stand in for a module the judge imports.
cd /tests

readonly VERDICT=/logs/verifier
readonly SCRATCH=/work
readonly RUNNER_ID=1002
readonly CLOCK=60
readonly EACH_FAMILY=40

# Root-only before any submitted line runs: the verdict directory, and the sealed model with the
# frozen answers. A process that outlives the run stage still cannot open either.
mkdir -p "${VERDICT}"
chown root:root "${VERDICT}"
chmod 0700 "${VERDICT}"
echo 0 > /logs/verifier/reward.txt
chmod 0700 /tests/seal

# The generated launches exist only from here on. The judge reads its own copy of the seed from
# the verdict directory; the run stage gets a copy it can overwrite without moving the exam.
python3 -I -c 'import secrets; print(secrets.token_hex(16))' > "${VERDICT}/nonce"
printf '%s\n' "${EACH_FAMILY}" > "${VERDICT}/per"
install -d -m 0755 -o "${RUNNER_ID}" -g "${RUNNER_ID}" "${SCRATCH}"
cp "${VERDICT}/nonce" "${VERDICT}/per" "${SCRATCH}/"
chown "${RUNNER_ID}:${RUNNER_ID}" "${SCRATCH}/nonce" "${SCRATCH}/per"

run_status=0
setpriv --reuid="${RUNNER_ID}" --regid="${RUNNER_ID}" --clear-groups \
  timeout "${CLOCK}" setsid --wait python3 /tests/worker.py --out "${SCRATCH}/worker_out.json" \
  || run_status=$?
echo "run stage exit status: ${run_status}"

python3 -I /tests/reap.py || true

judge_status=0
python3 -I -m pytest /tests/test_outputs.py -q -p no:cacheprovider --ctrf "${VERDICT}/ctrf.json" \
  || judge_status=$?

if (( run_status == 0 && judge_status == 0 )); then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
