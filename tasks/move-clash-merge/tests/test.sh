#!/bin/bash
# The verifier's entry point. The order is the point of it.
#
# First the reward channel is locked down and defaulted to 0, and the files a run must never
# read - the ground truth, the sealed model, the generator, the enumerated set, the grader -
# are made root-only. Then root builds the scenario list, which needs the model and so cannot
# happen inside the process that runs submitted code. Then a fresh work tree is assembled from
# the pristine copy with only the five declared artifacts laid over it, owned by root and
# read-only to the run. Then the run happens as an unprivileged uid, in its own session, under
# a hard timeout, reporting into a file root opened and handed down as a descriptor, so the uid
# executing agent code owns nothing it is graded on. Then survivors are reaped, and only then
# does pytest run, as root, never importing anything the agent wrote.
#
# The nonce attests this run and seeds the generated families.
set -Eeuo pipefail

install -d -m 700 -o root -g root /logs/verifier
echo 0 > /logs/verifier/reward.txt

chown root:root /tests/gt.json /tests/model.py /tests/gen.py /tests/cases.py \
                /tests/plant.py /tests/test_outputs.py
chmod 600 /tests/gt.json /tests/model.py /tests/gen.py /tests/cases.py \
          /tests/plant.py /tests/test_outputs.py

rm -rf /work
mkdir -p /work/app /work/run
cp -a /pristine/. /work/app/
# A declared file the agent never produced does not exist here; the pristine one stands in
# and the run fails on the answers. `[ -f ... ] && cp` would abort under `set -e` instead.
for f in mrg/live.py mrg/spot.py mrg/name.py mrg/book.py mrg/step.py; do
  if [ -f "/app/$f" ]; then
    cp -f "/app/$f" "/work/app/$f"
  fi
done
find /work/app \( -name __pycache__ -o -name '*.pyc' \) -exec rm -rf {} + 2>/dev/null || true
chown -R root:root /work
chmod -R u=rwX,go=rX /work/app
chmod 755 /work /work/run
install -d -m 700 -o merge -g merge /work/scratch

RUN_NONCE="$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
RUN_COUNT="${RUN_COUNT:-60}"
export RUN_NONCE RUN_COUNT
printf '%s\n' "$RUN_NONCE" > /logs/verifier/nonce

python /tests/plant.py /work/run/plan.json
chown root:root /work/run/plan.json
chmod 644 /work/run/plan.json

: > /work/run/out.json
chmod 600 /work/run/out.json

set +e
exec 9>/work/run/out.json
setsid --wait env APPDIR=/work/app HOME=/work/scratch TMPDIR=/work/scratch \
    PYTHONDONTWRITEBYTECODE=1 PLAN=/work/run/plan.json RUN_NONCE="$RUN_NONCE" \
  setpriv --reuid=1004 --regid=1004 --clear-groups \
  timeout --signal=KILL 600 python /tests/runner.py fd:9
run_status=$?
exec 9>&-
python /tests/reap.py 1004
reap_status=$?
set -e
[ "$run_status" -eq 0 ] && [ "$reap_status" -eq 0 ] || exit 1

if RUN_OUT=/work/run/out.json PLAN=/work/run/plan.json PRISTINE_DIR=/pristine \
   RUN_COUNT="$RUN_COUNT" REQUIRE_MONITORING=1 \
   pytest -rA --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
