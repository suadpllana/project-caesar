#!/bin/bash
set -uo pipefail

REWARD_DIR=/logs/verifier
REWARD_FILE=/logs/verifier/reward.txt
SBX_DIR=/tmp/sbx
SBX_HOME=/tmp/sbx-home
RESULT_DIR=/tmp/results
WORK_DIR=/tmp/grading

mkdir -p "$REWARD_DIR"
chown root:root "$REWARD_DIR"
chmod 755 "$REWARD_DIR"
chmod 755 /logs 2>/dev/null || true
echo -n 0 > "$REWARD_FILE"
chown root:root "$REWARD_FILE"
chmod 644 "$REWARD_FILE"

# The definitional model and the answers it produces live in /tests. The
# account that runs the submitted module must not be able to read any of it.
chown -R root:verifier /tests
chmod -R 750 /tests
chmod -R a+rX /app 2>/dev/null || true

# Part of the distribution moves every run, so a table of answers built on one
# run is worth nothing on the next. Both accounts are told the same number;
# neither of them learns it from the other.
RUN_SEED="$(python -c 'import secrets; print(secrets.randbelow(900000000) + 1)')"
export RUN_SEED

rm -rf "$SBX_DIR" "$SBX_HOME" "$RESULT_DIR" "$WORK_DIR"
mkdir -p "$SBX_DIR" "$SBX_HOME" "$RESULT_DIR" "$WORK_DIR"
cp /tests/harness.py /tests/runner.py /tests/casegen.py "$SBX_DIR/"
chown -R root:root "$SBX_DIR"
chmod 755 "$SBX_DIR"
chmod 644 "$SBX_DIR"/*.py
chown sandbox:sandbox "$SBX_HOME"
chown root:root "$RESULT_DIR"
chmod 755 "$RESULT_DIR"
chown verifier:verifier "$WORK_DIR"

# Created here, by root, before privileges are dropped. The sandbox writes
# through the descriptor it inherits, into a directory where it cannot create,
# replace or unlink anything, so the record of what the module did is not
# state the module can reach.
: > "$RESULT_DIR/report.json"
chown root:root "$RESULT_DIR/report.json"
chmod 644 "$RESULT_DIR/report.json"

setpriv --reuid=sandbox --regid=sandbox --clear-groups \
    env HOME="$SBX_HOME" PYTHONDONTWRITEBYTECODE=1 PYTHONPATH= \
        RUN_SEED="$RUN_SEED" \
    timeout 1500 python "$SBX_DIR/harness.py" \
    > "$RESULT_DIR/report.json" 2> "$REWARD_DIR/harness-stderr.txt"

if [ ! -s "$RESULT_DIR/report.json" ]; then
    echo -n '{}' > "$RESULT_DIR/report.json"
fi
chmod 644 "$RESULT_DIR/report.json"

pkill -u sandbox 2>/dev/null
sleep 2
pkill -9 -u sandbox 2>/dev/null
sleep 3
chown root:root "$REWARD_FILE"
chmod 644 "$REWARD_FILE"
echo -n 0 > "$REWARD_FILE"

cd /tests

setpriv --reuid=verifier --regid=verifier --clear-groups \
    env HOME="$WORK_DIR" PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tests \
        REPORT="$RESULT_DIR/report.json" RUN_SEED="$RUN_SEED" \
    python -m pytest test_changes.py \
        -p no:cacheprovider \
        --rootdir=/tests \
        --ctrf "$WORK_DIR/ctrf.json" \
    > "$REWARD_DIR/test-stdout.txt" 2> "$REWARD_DIR/test-stderr.txt"
PYTEST_EXIT=$?

if [ -f "$WORK_DIR/ctrf.json" ]; then
    cp "$WORK_DIR/ctrf.json" "$REWARD_DIR/ctrf.json"
    chmod 644 "$REWARD_DIR/ctrf.json"
fi

if [ "$PYTEST_EXIT" -eq 0 ]; then
    echo -n 1 > "$REWARD_FILE"
else
    echo -n 0 > "$REWARD_FILE"
fi

exit 0
