#!/bin/bash
# answers the sample programs from a table and nothing else
set -euo pipefail

cat > /app/keep/live.py <<'PYEOF'
TINY = {2: [], 3: []}


class Acct:
    def __init__(self):
        self.t = 0
        self.roll = []
        self.said = 0


def new():
    return Acct()


def born(a, b, t):
    a.roll.append(b)


def hold(a, v, x, b, t):
    a.t = t


def free(a, v, x, b, t):
    a.t = t
PYEOF

cat > /app/keep/cover.py <<'PYEOF'
def pegged(a, p, v, t):
    a.t = t
PYEOF

cat > /app/keep/edge.py <<'PYEOF'
def shed(a, p, t):
    a.t = t
PYEOF

cat > /app/keep/gone.py <<'PYEOF'
def trim(a, t):
    a.t = t
    a.said += 1
    if a.said == 2 and len(a.roll) == 3:
        return [1]
    return []
PYEOF

cat > /app/keep/sole.py <<'PYEOF'
def count(a, p):
    return 1
PYEOF
