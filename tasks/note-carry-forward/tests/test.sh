#!/bin/bash
# Entry point. Locks the reward channel before anything else runs, assembles a
# work tree from the pristine copy with only the declared artifacts overlaid,
# runs the board under an unprivileged account, reaps whatever that account
# left behind, and only then grades as root.
set -u

mkdir -p /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt
chmod 600 /logs/verifier/reward.txt

WORK=/work
rm -rf "${WORK}"
mkdir -p "${WORK}/app"
cp -a /pristine/. "${WORK}/app"

for rel in note/board.py note/rule.py; do
    if [ -f "/app/${rel}" ]; then
        mkdir -p "${WORK}/app/$(dirname "${rel}")"
        cp "/app/${rel}" "${WORK}/app/${rel}"
    fi
done

cp /tests/scen.py "${WORK}/scen.py"
cp /tests/runner.py "${WORK}/runner.py"
chown -R sandbox:sandbox "${WORK}"
chmod 755 "${WORK}"

: > "${WORK}/out.json"
chown root:root "${WORK}/out.json"
chmod 666 "${WORK}/out.json"

RUN_SEED="${RUN_SEED:-$(python3 -c 'import random;print(random.randrange(1,10**6))')}"
export RUN_SEED
export RUN_COUNT="${RUN_COUNT:-300}"

setsid --wait env APPDIR="${WORK}/app" RUN_SEED="${RUN_SEED}" \
    RUN_COUNT="${RUN_COUNT}" PYTHONPATH="${WORK}" \
    setpriv --reuid=1002 --regid=1002 --clear-groups \
    timeout --signal=KILL 600 \
    bash -c 'exec 9>>'"${WORK}"'/out.json; OUT_FD=9 python3 '"${WORK}"'/runner.py' \
    > /dev/null 2>&1

python3 /tests/reap.py 1002

cd /tests
if RUN_SEED="${RUN_SEED}" RUN_COUNT="${RUN_COUNT}" PYTHONPATH=/tests \
        python3 -m pytest /tests/test_outputs.py -q -rf --tb=line \
        --ctrf /logs/verifier/ctrf.json > /logs/verifier/pytest.log 2>&1; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
cat /logs/verifier/pytest.log
