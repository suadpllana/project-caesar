#!/bin/bash
# one fixed output for every script
set -euo pipefail

cat > /app/lk/mode.py <<'PYEOF'
UP = {
    "IS": frozenset(("IS",)),
    "IX": frozenset(("IS", "IX")),
    "S": frozenset(("IS", "S")),
    "SIX": frozenset(("IS", "IX", "SIX")),
    "X": frozenset(("IS", "IX", "SIX", "X")),
}

BAD = {
    "IS": frozenset(("X",)),
    "IX": frozenset(("S", "SIX", "X")),
    "S": frozenset(("IX", "SIX", "X")),
    "SIX": frozenset(("IX", "S", "SIX", "X")),
    "X": frozenset(("IS", "IX", "S", "SIX", "X")),
}

JOIN = {
    ("IS", "IS"): "IS", ("IS", "IX"): "IX", ("IS", "S"): "S",
    ("IS", "SIX"): "SIX", ("IS", "X"): "X",
    ("IX", "IX"): "IX", ("IX", "S"): "SIX", ("IX", "SIX"): "SIX", ("IX", "X"): "X",
    ("S", "S"): "S", ("S", "SIX"): "SIX", ("S", "X"): "X",
    ("SIX", "SIX"): "SIX", ("SIX", "X"): "X",
    ("X", "X"): "X",
}

NEED = {"S": "IS", "X": "IX"}


def ge(a, b):
    return b in UP[a]


def hits(a, b):
    return b in BAD[a]


def cover(a, b):
    if a is None:
        return b
    if b is None:
        return a
    got = JOIN.get((a, b))
    if got is None:
        got = JOIN.get((b, a))
    return got
PYEOF

cat > /app/lk/ent.py <<'PYEOF'
from . import mode


class Item:
    __slots__ = ("tid", "seq", "m", "conv")

    def __init__(self, tid, seq, m, conv):
        self.tid = tid
        self.seq = seq
        self.m = m
        self.conv = conv


class Ent:
    __slots__ = ("res", "held", "q")

    def __init__(self, res):
        self.res = res
        self.held = {}
        self.q = []

    def group(self):
        out = None
        for v in self.held.values():
            out = mode.cover(out, v)
        return out

    def hits_but(self, tid, m):
        g = self.group()
        return g is not None and mode.hits(g, m)

    def foes(self, tid, m):
        bad = mode.BAD[m]
        return [k for k, v in self.held.items() if k != tid and v in bad]

    def waiting(self):
        return bool(self.q)

    def head(self):
        return self.q[0]

    def queued(self):
        return list(self.q)

    def push(self, it):
        self.q.append(it)

    def pop_head(self):
        return self.q.pop(0)

    def drop_wait(self, tid):
        for i, it in enumerate(self.q):
            if it.tid == tid:
                del self.q[i]
                return it
        return None
PYEOF

cat > /app/lk/txn.py <<'PYEOF'
class Txn:
    __slots__ = ("tid", "seq", "state", "held", "seen", "pend")

    def __init__(self, tid, seq):
        self.tid = tid
        self.seq = seq
        self.state = "run"
        self.held = {}
        self.seen = {}
        self.pend = None

    def take(self, res, m, tbl, row):
        self.held[res] = m

    def drop(self, res, tbl, row):
        self.held.pop(res, None)

    def bump(self, tbl):
        self.seen[tbl] = self.seen.get(tbl, 0) + 1

    def tally(self, tbl):
        return self.seen.get(tbl, 0)


def standing(t, skip, ents):
    return t.seq
PYEOF

cat > /app/lk/ask.py <<'PYEOF'
class Engine:
    def __init__(self, out):
        self.out = out
        self.esc = 0
        self.ents = {}
        self.txns = {}
        self.order = []
        self.cov = 0

    def step(self, cmd):
        return
PYEOF

cat > /app/lk/wake.py <<'PYEOF'
class Wake:
    __slots__ = ("eng", "line")

    def __init__(self, eng):
        self.eng = eng
        self.line = []

    def touch(self, res):
        if res not in self.line:
            self.line.append(res)

    def settle(self):
        eng = self.eng
        while self.line:
            res = self.line.pop(0)
            e = eng.ents.get(res)
            if e is None:
                continue
            while e.waiting():
                before = len(e.q)
                eng.examine(e)
                if len(e.q) == before:
                    break
PYEOF

cat > /app/lk/lift.py <<'PYEOF'
from . import log, mode, read


def rows_of(t, tbl):
    out = []
    for res, m in t.held.items():
        k, row = read.split_res(res)
        if row >= 0 and k == tbl:
            out.append((res, m))
    return out


def subsume(eng, t, tbl, m):
    for res, _held in rows_of(t, tbl):
        eng.free(t, res)


def lift(eng, t, tbl):
    if t.tally(tbl) < eng.esc:
        return
    bag = rows_of(t, tbl)
    if not bag:
        return
    want = "S"
    for _res, v in bag:
        if v != "S":
            want = "X"
            break
    res = str(tbl)
    cur = t.held.get(res)
    if cur is not None and mode.ge(cur, want):
        return
    tgt = mode.cover(cur, want)
    e = eng.ents.get(res)
    if e is not None and e.hits_but(t.tid, tgt):
        for tid in e.foes(t.tid, tgt):
            h = eng.txns.get(tid)
            if h is not None and t.seq < h.seq:
                eng.fell(t, h)
        if e.hits_but(t.tid, tgt):
            return
    eng.out.append(log.es(t.tid, res, tgt))
    eng.grant(t, res, tgt)
PYEOF

cat > /app/lk/tell.py <<'PYEOF'
def report(eng):
    return ["cov 0"]
PYEOF
