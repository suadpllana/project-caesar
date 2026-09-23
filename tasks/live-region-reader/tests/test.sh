#!/bin/bash
# live-region-reader verifier.
#
# The submitted reader is run exactly once, as its own unprivileged uid, and all it does is write
# down the log every graded page printed. Root grades that record afterwards without running any
# of it. reward.txt says 0 from the first line below until both of those came back clean.
set -euo pipefail

readonly READER_UID=1002
readonly CLOCK_SECONDS=60
readonly PER_FAMILY=30

# Before anything submitted exists as a process: the reward directory and the sealed model are
# root's alone.
install -d -m 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt
chmod 700 /tests/seal

# The generated pages are drawn from a seed made here, after the agent's container is gone. Root
# grades against its own copy; the reader gets another in /work, and rewriting that one changes
# nothing about the exam.
python3 -c "import secrets; print(secrets.token_hex(16))" > /logs/verifier/nonce
echo "${PER_FAMILY}" > /logs/verifier/per
install -d -m 755 -o "${READER_UID}" -g "${READER_UID}" /work
for f in nonce per; do
    install -m 644 -o "${READER_UID}" -g "${READER_UID}" "/logs/verifier/${f}" "/work/${f}"
done

# This one wall clock is the execution limit the brief states: the whole graded set, the wide
# and held pages included, inside it.
reader_status=0
setpriv --reuid="${READER_UID}" --regid="${READER_UID}" --clear-groups \
    timeout "${CLOCK_SECONDS}" setsid --wait \
    python3 /tests/worker.py --out /work/worker_out.json || reader_status=$?
echo "reader exited with ${reader_status}"

python3 /tests/reap.py || true

grade_status=0
python3 -m pytest /tests/test_outputs.py -p no:cacheprovider -q \
    --ctrf /logs/verifier/ctrf.json || grade_status=$?

if [ "${reader_status}" -eq 0 ] && [ "${grade_status}" -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
