#!/bin/bash
# relaxes until nothing moves, updating in place, so a binding carried onward before its second route arrives is never withdrawn
set -euo pipefail

cat > /app/res/step.py <<'PYEOF'
from prog.deck import UNIT, at
from prog.unit import find


def cost(rs, rv):
    return (rs if rs > rv else rv) + 1


def srcs(deck, prog, u, s):
    out = []
    b = at(deck, u.nm, s)
    if b is not None and b[0] == UNIT:
        out.append((b[1], b[2]))
    if find(prog, s) is not None:
        out.append((s, 0))
    return out
PYEOF

cat > /app/res/show.py <<'PYEOF'
from prog.deck import CLASH, at, row
from prog.unit import find


def out_all(deck, prog, vn):
    v = find(prog, vn)
    if v is None:
        return ()
    got = []
    for x, b in row(deck, vn).items():
        if b[0] == CLASH or x in v.hides or x in v.shuts:
            continue
        got.append((x, b))
    return got


def out_one(deck, prog, vn, x):
    v = find(prog, vn)
    if v is None:
        return None
    b = at(deck, vn, x)
    if b is None or b[0] == CLASH or x in v.hides:
        return None
    return b
PYEOF

cat > /app/res/pick.py <<'PYEOF'
from prog.deck import CLASH


def settle(cands):
    head = cands[0]
    for c in cands:
        if c != head:
            return (CLASH, None)
    return head
PYEOF

cat > /app/res/turn.py <<'PYEOF'
from prog.deck import OWN, UNIT, at, blank, put
from prog.unit import find

from .pick import settle
from .show import out_all, out_one
from .step import cost, srcs


def gather(deck, prog, u):
    got = {}
    for x in u.owns:
        got.setdefault(x, []).append((OWN, u.nm, 0))
    for x, vn in u.als:
        if find(prog, vn) is not None:
            got.setdefault(x, []).append((UNIT, vn, 0))
    for s, what in u.pulls:
        for vn, rs in srcs(deck, prog, u, s):
            if what == "*":
                for x, b in out_all(deck, prog, vn):
                    got.setdefault(x, []).append((b[0], b[1], cost(rs, b[2])))
            else:
                b = out_one(deck, prog, vn, what)
                if b is not None:
                    got.setdefault(what, []).append((b[0], b[1], cost(rs, b[2])))
    return got


def run(prog):
    deck = blank(prog.units)
    for _ in range(4000):
        moved = False
        for u in prog.units.values():
            for x, cands in gather(deck, prog, u).items():
                low = min(c[2] for c in cands)
                kind, tgt = settle([(c[0], c[1]) for c in cands if c[2] == low])
                if at(deck, u.nm, x) != (kind, tgt, low):
                    put(deck, u.nm, x, kind, tgt, low)
                    moved = True
        if not moved:
            break
    return deck
PYEOF

