#!/bin/bash
# Verifier entry point for line-step-stop. Runs as root in the verifier container.
#
# The reward channel is locked and set to 0 before any submitted code runs, and it is only
# written to 1 at the very end, by this script, when both the trusted judge and the pytest
# report exit cleanly. Submitted code runs only inside the judge's worker processes, under an
# unprivileged user that can read neither /tests/seal nor /logs/verifier nor the verdict.
set -euo pipefail
mkdir -p /logs/verifier
chmod 700 /logs/verifier
echo 0 > /logs/verifier/reward.txt
chown -R root:root /tests/seal
chmod 700 /tests/seal
chmod 755 /tests /tests/base

judge=0
python3 /tests/judge.py || judge=$?

report=0
pytest --ctrf /logs/verifier/ctrf.json /tests/test_stops.py -rA || report=$?

if [ "$judge" -eq 0 ] && [ "$report" -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
