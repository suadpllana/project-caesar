#!/bin/bash
# Verifier entry point. Runs as root in a separate container built from tests/Dockerfile.
#
# The reward is NOT derived from pytest's exit status. Agent-supplied code is executed,
# so an exit status is something the deliverable could produce on its own. Instead:
#
#   1. /logs/verifier is made root-only before anything runs, so no process the agent
#      can influence is able to write reward.txt or plant a CTRF report.
#   2. /tests is made unreadable to the unprivileged user, and the only file that user
#      needs, the sandboxed worker, is copied out to /run/worker.py first.
#   3. pytest runs the suite. It never imports the agent's code: everything that touches
#      /app happens in tests/worker.py, which the harness launches through setpriv as
#      nobody with --no-new-privs.
#   4. Anything still running as that user is killed before grading.
#   5. tests/grade.py, a fresh root process that imports nothing from /app, requires the
#      CTRF report to show every expected test executed and passed, with a start time
#      after this script began. Only then is 1 written.
#
# Keep every Python version pinned with ==. Never version-pin apt packages.

set -uo pipefail

REPORT=/logs/verifier/ctrf.json
UNPRIVILEGED_UID=65534

mkdir -p /logs/verifier
chown root:root /logs/verifier
chmod 700 /logs/verifier
rm -f "$REPORT" /logs/verifier/reward.txt

# Record when this run began, so a report planted earlier cannot be counted.
STARTED_MS=$(python3 -c 'import time; print(int(time.time() * 1000) - 1000)')

install -m 0755 -o root -g root /tests/worker.py /run/worker.py
chmod 700 /tests

find /app -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null

python3 -m pytest --ctrf "$REPORT" /tests/test_outputs.py -rA -p no:cacheprovider
PYTEST_STATUS=$?

# A daemonized child of the agent's code must not outlive the run and touch anything.
pkill -9 -u "$UNPRIVILEGED_UID" 2>/dev/null
sleep 1

python3 /tests/grade.py "$REPORT" /tests/expected_tests.txt "$PYTEST_STATUS" "$STARTED_MS"
GRADE_STATUS=$?

if [ $GRADE_STATUS -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi

chmod 755 /logs/verifier
chmod 644 /logs/verifier/reward.txt
[ -f "$REPORT" ] && chmod 644 "$REPORT"

exit 0
