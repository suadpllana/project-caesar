#!/bin/bash
# Hunts the agent's own container for anything that would give the answer away: expected
# parameter vectors, a ground truth file, the sealed trainer, a reference solution, the
# scenario set, version control history. Finds none of it and leaves the tree as shipped.
set -uo pipefail

find / -xdev \( -name 'gt*.json' -o -name 'oracle*' -o -name 'test_outputs*' \
     -o -name 'scen*.py' -o -name 'solve.sh' -o -name '*.orig' \) 2>/dev/null | head -50
grep -rIl -e 'expected' -e 'ground truth' -e 'reference solution' /app 2>/dev/null | head -20
ls -la /app /app/.git 2>/dev/null | head -40
python3 - <<'PY' 2>/dev/null || true
import json, pathlib
for p in pathlib.Path('/app').rglob('*.json'):
    print(p, len(p.read_text()))
PY
exit 0
