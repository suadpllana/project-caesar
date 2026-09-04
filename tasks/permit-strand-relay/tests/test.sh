#!/bin/bash
# Deny first, then build the work tree, then run, then reap, then grade.
#
# The reward file is written and locked before anything else happens, so a run
# that dies half way through leaves a 0 rather than whatever was there before.
# The nonce that picks the generated half of the graded set is drawn here,
# after the agent has stopped, and handed to the run and to the grader.
set -u

install -d -m 700 /logs/verifier
printf '0\n' > /logs/verifier/reward.txt
chmod 600 /logs/verifier/reward.txt

CELL=/work
rm -rf "${CELL}"
install -d "${CELL}"
cp -a /pristine "${CELL}/app"

for leaf in adm.py rtn.py tear.py emit.py; do
    if [ -f "/app/pol/${leaf}" ]; then
        cp "/app/pol/${leaf}" "${CELL}/app/pol/${leaf}"
    fi
done

cp /tests/runner.py /tests/cases.py /tests/gen.py "${CELL}/"
chown -R sandbox:sandbox "${CELL}"
chmod 755 "${CELL}"

: > "${CELL}/report.json"
chown root:root "${CELL}/report.json"
chmod 666 "${CELL}/report.json"

RUN_NONCE="${RUN_NONCE:-$(od -An -N4 -tu4 /dev/urandom | tr -d ' \n')}"
RUN_WIDE="${RUN_WIDE:-300}"
export RUN_NONCE RUN_WIDE

setsid --wait env APPDIR="${CELL}/app" RUN_NONCE="${RUN_NONCE}" \
    RUN_WIDE="${RUN_WIDE}" PYTHONPATH="${CELL}" \
    setpriv --reuid=1002 --regid=1002 --clear-groups \
    timeout --signal=KILL 600 \
    bash -c 'exec 7>>'"${CELL}"'/report.json; SINK_FD=7 python3 '"${CELL}"'/runner.py' \
    > /dev/null 2>&1

python3 /tests/reap.py 1002

if RUN_NONCE="${RUN_NONCE}" RUN_WIDE="${RUN_WIDE}" PYTHONPATH=/tests \
        python3 -m pytest /tests/test_outputs.py -q -rf --tb=line \
        --ctrf /logs/verifier/ctrf.json > /logs/verifier/pytest.log 2>&1; then
    printf '1\n' > /logs/verifier/reward.txt
else
    printf '0\n' > /logs/verifier/reward.txt
fi
cat /logs/verifier/pytest.log
