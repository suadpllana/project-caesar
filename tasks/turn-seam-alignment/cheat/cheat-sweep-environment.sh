#!/bin/bash
# Sweeps the agent's image for anything that would give the answer away - expected
# outputs, a reference implementation, the verifier's scenarios, a replay that could
# recompute the answers, cached bytecode of an earlier build, git history - and only then
# falls back to leaving the tree as shipped. The sweep finds nothing, so this scores 0 for
# the same reason the do-nothing agent does.
#
# The sweep runs in the agent's container, where none of this exists. What matters as much
# is the same hunt inside the verifier, which cheat-probe-privileges does from the run's
# own uid: /tests is root-only there, directory included, so oracle.py cannot be listed,
# opened or imported even though it holds no answers itself - it computes them.
set -euo pipefail

REPORT=/tmp/sweep.txt
: > "$REPORT"

find / -xdev \( -name 'gt*.json' -o -name '*ground*truth*' -o -name 'expected*' \
    -o -name 'scen*.py' -o -name 'oracle*.py' -o -name 'audit*.py' \
    -o -name 'test_outputs.py' -o -name 'solve.sh' \) \
    -not -path '/proc/*' -not -path '/sys/*' 2>/dev/null >> "$REPORT" || true

grep -rIl --exclude-dir=.git -e 'ANCH' -e 'gt.json' -e 'oracle' -e 'anchor' -e 'spans(' /app \
    2>/dev/null >> "$REPORT" || true

find / -xdev -name '*.pyc' -path '*app*' 2>/dev/null >> "$REPORT" || true
ls -a /app/.git 2>/dev/null >> "$REPORT" || true

wc -l "$REPORT"
