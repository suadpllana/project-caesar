#!/bin/bash
set -uo pipefail

REWARD_DIR=/logs/verifier
SBX_DIR=/tmp/sbx
RESULT_DIR=/tmp/results
WORK_DIR=/tmp/grading

mkdir -p "$REWARD_DIR"
chown root:root "$REWARD_DIR"
chmod 755 "$REWARD_DIR"
chmod 755 /logs 2>/dev/null || true
echo 0 > /logs/verifier/reward.txt
chown root:root "$REWARD_DIR/reward.txt"
chmod 644 "$REWARD_DIR/reward.txt"

# One seed for the whole run, drawn here by root. The harness plans a workload
# from it and the grader works out that workload's answers from it, so neither
# side takes the other's word for which questions were asked.
RUN_SEED=$(python -c 'import secrets; print(secrets.randbelow(2**31))')
export RUN_SEED

# oracle.py is the definition of the right answer. The account that runs the
# submitted planner must not be able to read it, or the answer key is the task.
chown -R root:grading /tests
chmod -R 750 /tests
chmod -R a+rX /app 2>/dev/null || true

rm -rf "$SBX_DIR" "$RESULT_DIR" "$WORK_DIR"
mkdir -p "$SBX_DIR" "$RESULT_DIR" "$WORK_DIR"
cp /tests/harness.py "$SBX_DIR/harness.py"
cp /tests/runner.py "$SBX_DIR/runner.py"
cp /tests/casegen.py "$SBX_DIR/casegen.py"
chown -R sandbox:sandbox "$SBX_DIR"
chmod 755 "$SBX_DIR"
chmod 644 "$SBX_DIR"/*.py
chown root:root "$RESULT_DIR"
chmod 755 "$RESULT_DIR"
chown grading:grading "$WORK_DIR"

# Created here, by root, before privileges drop. The sandbox writes through the
# descriptor it inherits and cannot create, replace or unlink anything in this
# directory, so what the planner did is not a record the planner can edit.
: > "$RESULT_DIR/report.json"
chown root:root "$RESULT_DIR/report.json"
chmod 644 "$RESULT_DIR/report.json"

setpriv --reuid=sandbox --regid=sandbox --clear-groups \
    env HOME="$SBX_DIR" PYTHONDONTWRITEBYTECODE=1 PYTHONPATH= \
        RUN_SEED="$RUN_SEED" \
    timeout 2100 python "$SBX_DIR/harness.py" \
    > "$RESULT_DIR/report.json" 2> "$REWARD_DIR/harness-stderr.txt"

# Nothing belonging to the sandbox account outlives the run, and the reward is
# put back the way it started before a single answer is looked at.
pkill -u sandbox 2>/dev/null || true
sleep 2
pkill -9 -u sandbox 2>/dev/null || true
sleep 3
if pgrep -u sandbox > /dev/null 2>&1; then
    echo "processes from the sandbox account survived the run" \
        >> "$REWARD_DIR/harness-stderr.txt"
fi
chown root:root "$REWARD_DIR" "$REWARD_DIR/reward.txt"
chmod 755 "$REWARD_DIR"
chmod 644 "$REWARD_DIR/reward.txt"
echo 0 > /logs/verifier/reward.txt

if [ ! -s "$RESULT_DIR/report.json" ]; then
    echo -n '{}' > "$RESULT_DIR/report.json"
fi
chmod 644 "$RESULT_DIR/report.json"
cp "$RESULT_DIR/report.json" "$REWARD_DIR/report.json" 2>/dev/null || true

cd /tests

setpriv --reuid=grading --regid=grading --clear-groups \
    env HOME="$WORK_DIR" PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tests \
        REPORT="$RESULT_DIR/report.json" RUN_SEED="$RUN_SEED" \
    python -m pytest test_reads.py \
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
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi

exit 0
