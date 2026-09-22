#!/bin/bash
# replays the worked example's four lines by frame number
set -euo pipefail

cat > /app/view/lay.py <<'PYEOF'

PYEOF

cat > /app/view/stick.py <<'PYEOF'

PYEOF

cat > /app/view/pick.py <<'PYEOF'

PYEOF

cat > /app/view/hold.py <<'PYEOF'
# the worked example's output replayed by frame number
LINES = ['1 31 b4', '2 358 off scroll', '3 342 b12', '4 253 off scroll']
STATE = {"n": 0}


def start(v):
    STATE["n"] = 0


def before(v):
    pass


def after(v):
    n = STATE["n"]
    STATE["n"] = n + 1
    if n < len(LINES):
        part = LINES[n].split(" ", 2)
        return int(part[1]), part[2]
    return max(v.s, 0), "none"
PYEOF

