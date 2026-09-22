#!/bin/bash
# every expression comes back with no binding
set -euo pipefail

cat > /app/res/kind.py <<'PYEOF'
def steps(prog, a, b):
    if a == b:
        return 0
    for nxt in prog.ups.get(a, ()):
        got = steps(prog, nxt, b)
        if got is not None:
            return got + 1
    return None
PYEOF

cat > /app/res/pick.py <<'PYEOF'
from res import kind


def cands(prog, name, count):
    return [ent for ent in prog.entries
            if ent.name == name and len(ent.params) == count]


def opens(ent):
    return [i for i, p in enumerate(ent.params) if p == "*"]


def slots(ent, settled):
    return [settled if p == "*" else p for p in ent.params]


def result(ent, settled):
    return settled if ent.ret == "*" else ent.ret


def in_bound(prog, ent, settled):
    return kind.steps(prog, ent.bound, settled) is not None
PYEOF

cat > /app/res/pin.py <<'PYEOF'
from res import kind


def settle(prog, sources):
    high = sources[0]
    for one in sources[1:]:
        if kind.steps(prog, high, one) is not None:
            high = one
    return high
PYEOF

cat > /app/res/cost.py <<'PYEOF'
from res import kind


def slot(prog, stands, asked):
    return kind.steps(prog, stands, asked)


def result(prog, gives, expected):
    if expected is None:
        return 0
    if kind.steps(prog, gives, expected) is None:
        return None
    return 0
PYEOF

cat > /app/res/best.py <<'PYEOF'
def winner(vecs):
    low = min(sum(vec) for vec in vecs)
    same = [i for i, vec in enumerate(vecs) if sum(vec) == low]
    if len(same) == 1:
        return same[0]
    return None
PYEOF

cat > /app/res/walk.py <<'PYEOF'
from res import spec


class State:
    def __init__(self, prog):
        self.prog = prog


def new(prog):
    return State(prog)


def total(state):
    return 0


def ask(state, node):
    return spec.Result("none", None, [], [])
PYEOF
