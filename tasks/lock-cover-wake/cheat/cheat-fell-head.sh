#!/bin/bash
# a waiting head fells what is in its way when it is looked at
set -euo pipefail

cat > /app/lk/mode.py <<'PYEOF'
MODES = ("IS", "IX", "S", "SIX", "X")

UP = {
    "IS": frozenset(("IS",)),
    "IX": frozenset(("IS", "IX")),
    "S": frozenset(("IS", "S")),
    "SIX": frozenset(("IS", "IX", "S", "SIX")),
    "X": frozenset(("IS", "IX", "S", "SIX", "X")),
}

BAD = {
    "IS": frozenset(("X",)),
    "IX": frozenset(("S", "SIX", "X")),
    "S": frozenset(("IX", "SIX", "X")),
    "SIX": frozenset(("IX", "S", "SIX", "X")),
    "X": frozenset(("IS", "IX", "S", "SIX", "X")),
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
    for m in MODES:
        up = UP[m]
        if a in up and b in up:
            return m
    return "X"
PYEOF

cat > /app/lk/ent.py <<'PYEOF'
from . import mode


class Item:
    __slots__ = ("tid", "seq", "m", "conv", "cont")

    def __init__(self, tid, seq, m, conv, cont):
        self.tid = tid
        self.seq = seq
        self.m = m
        self.conv = conv
        self.cont = cont


class Ent:
    __slots__ = ("res", "held", "cq", "nq", "old", "many")

    def __init__(self, res):
        self.res = res
        self.held = {}
        self.cq = []
        self.nq = []
        self.old = None
        self.many = {}

    def put(self, tid, m):
        was = self.held.get(tid)
        if was == m:
            return
        if was is not None:
            self.many[was] -= 1
        self.held[tid] = m
        self.many[m] = self.many.get(m, 0) + 1

    def lose(self, tid):
        was = self.held.pop(tid, None)
        if was is not None:
            self.many[was] -= 1

    def hits_but(self, tid, m):
        mine = self.held.get(tid)
        for bad in mode.BAD[m]:
            n = self.many.get(bad, 0)
            if n > (1 if mine == bad else 0):
                return True
        return False

    def foes(self, tid, m):
        bad = mode.BAD[m]
        return [k for k, v in self.held.items() if k != tid and v in bad]

    def waiting(self):
        return bool(self.cq) or bool(self.nq)

    def head(self):
        return self.cq[0] if self.cq else self.nq[0]

    def queued(self):
        return self.cq + self.nq

    def push(self, it):
        (self.cq if it.conv else self.nq).append(it)
        if self.old is None or it.seq < self.old:
            self.old = it.seq

    def pop_head(self):
        q = self.cq if self.cq else self.nq
        it = q.pop(0)
        if self.old == it.seq:
            self.recount()
        return it

    def drop_wait(self, tid):
        for q in (self.cq, self.nq):
            for i, it in enumerate(q):
                if it.tid == tid:
                    del q[i]
                    if self.old == it.seq:
                        self.recount()
                    return it
        return None

    def recount(self):
        best = None
        for q in (self.cq, self.nq):
            for it in q:
                if best is None or it.seq < best:
                    best = it.seq
        self.old = best
PYEOF

cat > /app/lk/txn.py <<'PYEOF'
import heapq


class Txn:
    __slots__ = ("tid", "seq", "state", "held", "rows", "pend", "hp")

    def __init__(self, tid, seq):
        self.tid = tid
        self.seq = seq
        self.state = "run"
        self.held = {}
        self.rows = {}
        self.pend = None
        self.hp = []

    def take(self, res, m, tbl, row):
        self.held[res] = m
        if row >= 0:
            b = self.rows.get(tbl)
            if b is None:
                b = self.rows[tbl] = {}
            b[res] = m

    def drop(self, res, tbl, row):
        self.held.pop(res, None)
        if row >= 0:
            b = self.rows.get(tbl)
            if b is not None:
                b.pop(res, None)
                if not b:
                    del self.rows[tbl]

    def tally(self, tbl):
        b = self.rows.get(tbl)
        return 0 if b is None else len(b)

    def note(self, res, val):
        heapq.heappush(self.hp, (val, res))


def standing(t, skip, ents):
    best = t.seq
    hp = t.hp
    aside = []
    while hp:
        val, res = hp[0]
        if res not in t.held:
            heapq.heappop(hp)
            continue
        e = ents.get(res)
        if e is None or e.old != val:
            heapq.heappop(hp)
            continue
        if res == skip:
            aside.append(heapq.heappop(hp))
            continue
        break
    if hp and hp[0][0] < best:
        best = hp[0][0]
    for it in aside:
        heapq.heappush(hp, it)
    return best
PYEOF

cat > /app/lk/ask.py <<'PYEOF'
from . import ent, lift, log, mode, read, txn, wake


class Engine:
    def __init__(self, out):
        self.out = out
        self.esc = 0
        self.ents = {}
        self.txns = {}
        self.order = []
        self.cov = 0
        self.wk = wake.Wake(self)

    def step(self, cmd):
        k = cmd[0]
        if k == "cfg":
            self.esc = cmd[1]
        elif k == "beg":
            tid = cmd[1]
            if tid in self.txns:
                return
            self.txns[tid] = txn.Txn(tid, len(self.order))
            self.order.append(tid)
        elif k == "req":
            t = self.txns.get(cmd[1])
            if t is None or t.state != "run":
                return
            self.ask(t, cmd[2], cmd[3])
            self.wk.settle()
        elif k == "com":
            t = self.txns.get(cmd[1])
            if t is None or t.state != "run":
                return
            self.let_go(t)
            t.state = "done"
            self.wk.settle()

    # --- the four ways a request ends: covered, granted, queued, felled -------------

    def ask(self, t, res, m):
        tbl, row = read.split_res(res)
        cur = t.held.get(res)
        if cur is not None and mode.ge(cur, m):
            self.cov += 1
            return
        if row >= 0:
            top = str(tbl)
            p = t.held.get(top)
            if p is not None and mode.ge(p, m):
                self.cov += 1
                return
            need = mode.NEED[m]
            if p is None or not mode.ge(p, need):
                self.place(t, top, mode.cover(p, need), (res, m))
                return
        self.place(t, res, m if cur is None else mode.cover(cur, m), None)

    def place(self, t, res, tgt, cont):
        e = self.ents.get(res)
        if e is None:
            e = self.ents[res] = ent.Ent(res)
        conv = t.tid in e.held
        if self.can(e, t.tid, tgt, conv):
            self.out.append(log.gr(t.tid, res, tgt))
            self.grant(t, res, tgt, cont)
            return
        for tid in sorted(e.foes(t.tid, tgt), key=lambda k: self.txns[k].seq):
            if tid not in e.held:
                continue
            h = self.txns[tid]
            if t.seq < txn.standing(h, res, self.ents):
                self.fell(t, h)
        if self.can(e, t.tid, tgt, conv):
            self.out.append(log.gr(t.tid, res, tgt))
            self.grant(t, res, tgt, cont)
            return
        e.push(ent.Item(t.tid, t.seq, tgt, conv, cont))
        self.shield(e)
        t.state = "wait"
        t.pend = res
        self.out.append(log.wt(t.tid, res, tgt))
        self.wk.touch(res)

    def can(self, e, tid, m, conv):
        if conv:
            if e.cq:
                return False
        elif e.cq or e.nq:
            return False
        return not e.hits_but(tid, m)

    # --- what a grant does beyond adding a holder ----------------------------------

    def grant(self, t, res, m, cont):
        e = self.ents.get(res)
        if e is None:
            e = self.ents[res] = ent.Ent(res)
        e.put(t.tid, m)
        tbl, row = read.split_res(res)
        t.take(res, m, tbl, row)
        if e.old is not None:
            t.note(res, e.old)
        self.wk.touch(res)
        if row < 0:
            lift.subsume(self, t, tbl, m)
        else:
            lift.lift(self, t, tbl)
        if cont is not None:
            self.ask(t, cont[0], cont[1])

    def examine(self, e):
        it = e.head()
        if e.hits_but(it.tid, it.m):
            t = self.txns[it.tid]
            for tid in sorted(e.foes(it.tid, it.m), key=lambda k: self.txns[k].seq):
                if tid not in e.held:
                    continue
                h = self.txns[tid]
                if t.seq < txn.standing(h, e.res, self.ents):
                    self.fell(t, h)
            if e.hits_but(it.tid, it.m):
                return
        e.pop_head()
        self.shield(e)
        self.wk.touch(e.res)
        t = self.txns[it.tid]
        t.state = "run"
        t.pend = None
        self.out.append(log.gr(t.tid, e.res, it.m))
        self.grant(t, e.res, it.m, it.cont)

    def fell(self, by, h):
        self.out.append(log.wd(by.tid, h.tid))
        if h.pend is not None:
            e = self.ents.get(h.pend)
            if e is not None:
                e.drop_wait(h.tid)
                self.shield(e)
                self.wk.touch(h.pend)
            h.pend = None
        self.let_go(h)
        h.state = "cut"

    # --- releasing ------------------------------------------------------------------

    def let_go(self, t):
        for res in list(t.held):
            self.free(t, res)

    def free(self, t, res):
        e = self.ents.get(res)
        if e is not None:
            e.lose(t.tid)
        tbl, row = read.split_res(res)
        t.drop(res, tbl, row)
        self.wk.touch(res)

    def shield(self, e):
        val = e.old
        if val is None:
            return
        for tid in e.held:
            self.txns[tid].note(e.res, val)
PYEOF

cat > /app/lk/wake.py <<'PYEOF'
import heapq


class Wake:
    __slots__ = ("eng", "hp", "dirty")

    def __init__(self, eng):
        self.eng = eng
        self.hp = []
        self.dirty = set()

    def touch(self, res):
        e = self.eng.ents.get(res)
        if e is None or not e.waiting():
            self.dirty.discard(res)
            return
        self.dirty.add(res)
        heapq.heappush(self.hp, (e.head().seq, res))

    def settle(self):
        eng = self.eng
        hp = self.hp
        while hp:
            seq, res = heapq.heappop(hp)
            if res not in self.dirty:
                continue
            e = eng.ents.get(res)
            if e is None or not e.waiting():
                self.dirty.discard(res)
                continue
            if e.head().seq != seq:
                continue
            self.dirty.discard(res)
            eng.examine(e)
PYEOF

cat > /app/lk/lift.py <<'PYEOF'
from . import log, mode


def subsume(eng, t, tbl, m):
    b = t.rows.get(tbl)
    if not b:
        return
    for res, held in list(b.items()):
        if mode.ge(m, held):
            eng.free(t, res)


def lift(eng, t, tbl):
    b = t.rows.get(tbl)
    if b is None or len(b) < eng.esc:
        return
    want = "S"
    for v in b.values():
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
        return
    eng.out.append(log.es(t.tid, res, tgt))
    eng.grant(t, res, tgt, None)
PYEOF

cat > /app/lk/tell.py <<'PYEOF'
from . import log, read


def report(eng):
    out = []
    for tid in eng.order:
        t = eng.txns[tid]
        out.append(log.tx(tid, t.state, list(t.held.items())))
    for res in sorted(eng.ents, key=read.split_res):
        e = eng.ents[res]
        if e.waiting():
            out.append(log.q(res, [(it.tid, it.m) for it in e.queued()]))
    out.append(log.cov(eng.cov))
    return out
PYEOF
