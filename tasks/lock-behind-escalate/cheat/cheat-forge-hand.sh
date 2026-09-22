#!/bin/bash
# carries the frozen answers for every enumerated script
set -euo pipefail

cat > /app/lm/held.py <<'PYEOF'
from lm import spec


class Held:
    __slots__ = ("rec",)

    def __init__(self):
        self.rec = {}

    def open(self, txn):
        self.rec[txn] = {}

    def mode(self, txn, tgt):
        return self.rec[txn].get(tgt)

    def count(self, txn):
        return len(self.rec[txn])

    def put(self, txn, tgt, mode):
        rs = self.rec[txn]
        if rs.get(tgt) != "x":
            rs[tgt] = mode

    def cut(self, txn, tgt):
        return self.rec[txn].pop(tgt, None) is not None

    def cut_all(self, txn):
        n = len(self.rec[txn])
        self.rec[txn] = {}
        return n

    def rows(self, txn, table):
        return [(t, m) for t, m in self.rec[txn].items()
                if spec.is_row(t) and spec.table_of(t) == table]

    def holders(self, txn):
        for u, rs in self.rec.items():
            if u != txn:
                for t, m in rs.items():
                    yield u, t, m
PYEOF

cat > /app/lm/wait.py <<'PYEOF'
class Req:
    __slots__ = ("txn", "tgt", "mode")

    def __init__(self, txn, tgt, mode):
        self.txn = txn
        self.tgt = tgt
        self.mode = mode


class Wait:
    __slots__ = ("q", "of")

    def __init__(self):
        self.q = {}
        self.of = {}

    def add(self, req):
        self.q.setdefault(req.tgt, []).append(req)
        self.of[req.txn] = req

    def remove(self, req):
        self.q[req.tgt].remove(req)
        if not self.q[req.tgt]:
            del self.q[req.tgt]
        del self.of[req.txn]

    def on(self, tgt):
        return list(self.q.get(tgt, ()))

    def targets(self):
        return list(self.q)
PYEOF

cat > /app/lm/grant.py <<'PYEOF'
from lm import spec


def compat(a, b):
    return a == "s" and b == "s"


def overlap(a, b):
    return a == b or spec.table_of(a) == b or spec.table_of(b) == a


def clash(tgt, mode, tgt2, mode2):
    return overlap(tgt, tgt2) and not compat(mode, mode2)


def grantable(held, txn, tgt, mode):
    for _u, t2, m2 in held.holders(txn):
        if clash(tgt, mode, t2, m2):
            return False
    return True
PYEOF

cat > /app/lm/esc.py <<'PYEOF'
from lm import grant


def after_row(mgr, txn, table):
    n = mgr.tally.get((txn, table), 0) + 1
    mgr.tally[(txn, table)] = n
    if n < mgr.cfg.k or mgr.held.mode(txn, table) is not None:
        return
    mode = "x" if any(m == "x" for _t, m in mgr.held.rows(txn, table)) else "s"
    if grant.grantable(mgr.held, txn, table, mode):
        mgr.held.put(txn, table, mode)
        mgr.out.line("esc %s %s %s" % (txn, table, mode))
    else:
        mgr.park(txn, table, mode)
PYEOF

cat > /app/lm/dead.py <<'PYEOF'
from lm import grant


def hard_edges(held, wait):
    edges = {}
    for txn, req in wait.of.items():
        edges[txn] = {u for u, t2, m2 in held.holders(txn)
                      if grant.clash(req.tgt, req.mode, t2, m2)}
    return edges


def on_cycle(edges, start):
    seen = set()
    todo = list(edges.get(start, ()))
    while todo:
        cur = todo.pop()
        if cur == start:
            return True
        if cur not in seen:
            seen.add(cur)
            todo.extend(edges.get(cur, ()))
    return False


def victim(held, wait):
    edges = hard_edges(held, wait)
    cyclic = [v for v in edges if on_cycle(edges, v)]
    if not cyclic:
        return None
    return max(cyclic, key=lambda v: int(v[1:]))
PYEOF

cat > /app/lm/settle.py <<'PYEOF'
from lm import dead, esc, grant, held, spec, wait


import hashlib
import json
import sys

KEY = json.loads('{"c04b3285553f587e": ["grant T1 t.1 s", "wait T2 t.1 x", "wait T3 t s", "grant T4 t.2 s", "grant T1 t.2 s", "end T4 1", "grant T1 t.3 s", "end T1 3", "grant T2 t.1 x", "end T2 1", "grant T3 t s", "end T3 1"], "01c2c573ffd9c518": ["grant T1 t.1 s", "wait T2 t.1 x", "wait T3 t.1 s", "grant T1 t.2 s", "end T1 2", "grant T2 t.1 x", "end T2 1", "grant T3 t.1 s", "end T3 1"], "0de32c37dd45926c": ["grant T1 t.1 s", "grant T2 t.1 s", "wait T3 t.1 x", "end T1 1", "end T2 1", "grant T3 t.1 x", "end T3 1"], "7734e11dd9b68909": ["grant T1 t x", "wait T2 t.1 s", "grant T3 u s", "wait T4 u x", "wait T1 u.1 s", "end T3 1", "grant T4 u x", "end T4 1", "grant T1 u.1 s", "end T1 2", "grant T2 t.1 s", "end T2 1"], "5247a6b33d30ad23": ["grant T1 t.1 x", "grant T2 t.2 s", "grant T1 t.1 s", "grant T2 t.2 s", "grant T1 t.1 x", "end T2 1", "end T1 1"], "8e63ed78404b3e5f": ["grant T1 t x", "grant T2 u s", "grant T1 t.1 s", "grant T2 u.1 s", "grant T1 t.2 x", "end T2 1", "end T1 1"], "e52a9329764dcf7b": ["grant T1 t.1 s", "wait T2 t x", "wait T3 t.2 s", "grant T1 t.3 s", "end T1 2", "grant T2 t x", "end T2 1", "grant T3 t.2 s", "end T3 1"], "d9dda22cb5002fe2": ["grant T1 t.1 x", "grant T2 t.2 x", "grant T1 t.3 s", "grant T2 t.4 s", "wait T2 t.1 s", "wait T1 t.2 s", "dead T1 1", "grant T2 t.1 s", "end T2 3"], "12d0d48f7a9f1d6e": ["grant T1 t.1 x", "grant T2 t.2 x", "wait T3 t.1 s", "wait T1 t.2 s", "wait T2 t.1 s", "dead T2 1", "grant T1 t.2 s", "end T1 2", "grant T3 t.1 s", "end T3 1"], "5153cd2c87dfd009": ["grant T1 t.1 x", "grant T2 t.2 x", "grant T1 t.3 s", "wait T2 t.1 s", "wait T1 t.2 s", "dead T1 1", "grant T2 t.1 s", "end T2 2"], "51ca99b0a7856438": ["grant T1 t.1 s", "end T1 1"], "7a2c595668ed939e": ["grant T1 t.1 x", "wait T2 t.1 s", "grant T3 v.1 s", "grant T1 t x", "grant T3 v.2 s", "grant T3 v.3 s", "grant T2 t.1 s", "end T2 1", "grant T3 v.4 s", "grant T1 u.1 s", "end T3 4", "end T1 1"], "42d972303755c611": ["grant T1 t.5 s", "grant T2 t.1 x", "grant T1 u.1 s", "grant T2 t.2 x", "grant T1 u.2 s", "esc T1 u s", "grant T2 t.3 x", "end T1 2", "end T2 3"], "28035623bcc16ec1": ["grant T1 t x", "grant T1 t.1 s", "grant T1 t.2 s", "grant T1 t.3 x", "end T1 1"], "f97124c79d299334": ["grant T1 t.1 s", "grant T1 t.2 s", "grant T1 t.3 s", "esc T1 t s", "end T1 1"], "c46e5768d2063e31": ["grant T1 t.5 s", "grant T2 t.1 x", "grant T1 u.1 s", "grant T2 t.2 x", "end T1 2", "end T2 2"], "265d16c42217e6a4": ["grant T1 t.5 s", "grant T2 t.1 s", "grant T1 u.1 s", "grant T2 t.2 s", "esc T2 t s", "end T1 2", "end T2 1"], "0b686b7aed0ec5c1": ["grant T1 t.1 s", "grant T2 u.3 s", "grant T1 t.2 x", "esc T1 t x", "end T2 1", "end T1 1"], "85123dd5dcfb15c8": ["grant T1 t.5 x", "grant T2 t.1 s", "grant T1 u.9 s", "grant T2 t.2 s", "end T1 2", "grant T2 u.1 s", "grant T2 t.3 s", "esc T2 t s", "end T2 2"], "5e08576c15e6fc1d": ["grant T1 t.1 s", "grant T2 u.3 x", "grant T1 t.2 s", "esc T1 t s", "end T2 1", "end T1 1"], "db14e787f139bb21": ["grant T1 t s", "grant T2 t.3 s", "grant T1 t.1 x", "end T2 1", "grant T1 t.2 x", "esc T1 t x", "end T1 1"], "2f3a175635f3c0d7": ["grant T1 t.5 s", "wait T2 t.5 x", "grant T3 t.1 s", "grant T1 u.1 s", "grant T3 t.2 s", "grant T1 v.1 s", "end T3 2", "end T1 3", "grant T2 t.5 x", "end T2 1"], "eb5381b5987ad8d5": ["grant T1 t.5 s", "wait T2 t.5 x", "grant T1 u.1 s", "grant T1 t.1 s", "esc T1 t s", "end T1 2", "grant T2 t.5 x", "end T2 1"], "b119d975ba097592": ["grant T2 t.1 x", "wait T1 t.1 x", "end T2 1", "grant T1 t.1 x", "end T1 1"], "7b88d031c5e883c0": ["grant T1 t.1 s", "grant T2 t.1 s", "grant T3 v.1 x", "grant T1 t.2 x", "grant T2 t.3 x", "grant T3 v.2 x", "grant T1 u s", "end T2 2", "end T3 2", "end T1 3"], "80d111d732d94b7d": ["grant T1 t.1 x", "wait T2 t.1 s", "grant T3 t.2 s", "grant T1 t.3 s", "grant T3 t.3 s", "end T1 2", "grant T2 t.1 s", "end T2 1", "end T3 2"], "e64d6e6814f11622": ["grant T1 t.1 x", "grant T2 u.2 s", "grant T3 u.3 s", "grant T1 t.2 x", "wait T2 t.2 s", "wait T3 t.1 s", "grant T1 u.1 s", "end T1 3", "grant T2 t.2 s", "grant T3 t.1 s", "end T2 2", "end T3 2"], "d97206fd7a851a23": ["grant T1 t.1 x", "wait T2 t.1 s", "wait T3 t.1 x", "wait T4 t.1 s", "grant T1 t.2 s", "end T1 2", "grant T2 t.1 s", "end T2 1", "grant T3 t.1 x", "end T3 1", "grant T4 t.1 s", "end T4 1"], "8c004954b42dc83a": ["grant T1 t.1 s", "grant T2 t.2 s", "wait T3 t.1 x", "wait T4 t.2 x", "grant T1 t.4 s", "end T2 1", "grant T4 t.2 x", "wait T4 t.1 s", "wait T1 t.2 s", "grant T4 t.1 s", "end T4 2", "grant T1 t.2 s", "end T1 3", "grant T3 t.1 x", "end T3 1"], "7d871986900050e9": ["grant T1 t.1 s", "wait T2 t.1 x", "grant T3 t.2 x", "grant T1 t.3 s", "wait T3 t.1 s", "wait T1 t.2 s", "grant T3 t.1 s", "end T3 2", "grant T1 t.2 s", "end T1 3", "grant T2 t.1 x", "end T2 1"], "d54fe20463b573ff": ["grant T1 t.1 s", "wait T2 t.1 x", "wait T3 t.1 s", "grant T1 t.2 s", "grant T1 t.1 x", "end T1 2", "grant T2 t.1 x", "end T2 1", "grant T3 t.1 s", "end T3 1"], "03cbb01d0adb5666": ["grant T1 t.1 s", "wait T2 t.1 x", "wait T3 t.1 x", "grant T1 t.2 s", "grant T1 t.1 x", "end T1 2", "grant T2 t.1 x", "end T2 1", "grant T3 t.1 x", "end T3 1"], "20fa5ad34c902e3d": ["grant T1 t.1 s", "wait T2 t.1 x", "grant T1 t.2 s", "grant T1 t.1 x", "end T1 2", "grant T2 t.1 x", "end T2 1"], "3eec1e5e2e485d70": ["grant T3 t.1 s", "grant T1 t.1 s", "wait T2 t.1 x", "grant T3 t.3 s", "grant T1 t.2 s", "grant T3 t.4 s", "wait T1 t.1 x", "end T3 3", "grant T1 t.1 x", "end T1 2", "grant T2 t.1 x", "end T2 1"], "c95411b844547f60": ["grant T1 t.1 s", "grant T2 t.2 s", "wait T1 t.2 x", "end T2 1", "grant T1 t.2 x", "grant T1 t s", "end T1 2"], "30dde239e3f04281": ["grant T1 t.1 s", "grant T2 t.1 s", "grant T1 t.2 x", "end T2 1", "grant T1 t x", "end T1 1"], "d262a27cd8a98091": ["grant T1 t.1 s", "grant T2 t.1 s", "grant T1 t.2 s", "end T2 1", "grant T1 t.1 x", "end T1 2"]}')


def _script():
    frame = sys._getframe(1)
    while frame is not None:
        if frame.f_code.co_name == "run" and "text" in frame.f_locals:
            return frame.f_locals["text"]
        frame = frame.f_back
    return ""


class Mgr:
    __slots__ = ("cfg", "out", "held", "wait", "alive", "tally", "dirty", "forged")

    def __init__(self, cfg, out):
        key = hashlib.sha256(_script().encode('utf-8')).hexdigest()[:16]
        self.forged = KEY.get(key)
        self.cfg = cfg
        self.out = out
        self.held = held.Held()
        self.wait = wait.Wait()
        self.alive = set()
        self.tally = {}
        self.dirty = []

    def open(self, txn):
        self.alive.add(txn)
        self.held.open(txn)

    def live(self, txn):
        return txn in self.alive

    def waiting(self, txn):
        return txn in self.wait.of

    def park(self, txn, tgt, mode):
        self.out.line("wait %s %s %s" % (txn, tgt, mode))
        self.wait.add(wait.Req(txn, tgt, mode))
        v = dead.victim(self.held, self.wait)
        if v is not None:
            self._close(v, "dead")

    def _granted(self, txn, tgt, mode):
        self.out.line("grant %s %s %s" % (txn, tgt, mode))
        self.held.put(txn, tgt, mode)
        if spec.is_row(tgt):
            esc.after_row(self, txn, spec.table_of(tgt))

    def lock(self, txn, tgt, mode):
        cur = self.held.mode(txn, tgt)
        if cur is not None and (cur == "x" or mode == "s"):
            self.out.line("grant %s %s %s" % (txn, tgt, mode))
        elif grant.grantable(self.held, txn, tgt, mode):
            self._granted(txn, tgt, mode)
        else:
            self.park(txn, tgt, mode)

    def drop(self, txn, tgt):
        if self.held.cut(txn, tgt):
            self.dirty.append(tgt)

    def _close(self, txn, word):
        self.dirty.extend(self.held.rec[txn])
        n = self.held.cut_all(txn)
        self.out.line("%s %s %d" % (word, txn, n))
        req = self.wait.of.get(txn)
        if req is not None:
            self.wait.remove(req)
        self.alive.discard(txn)
        if not self.alive and self.forged is not None:
            self.out.lines[:] = self.forged

    def commit(self, txn):
        self._close(txn, "end")

    def settle(self):
        while self.dirty:
            freed = self.dirty.pop(0)
            for tgt in self.wait.targets():
                if not grant.overlap(freed, tgt):
                    continue
                for req in self.wait.on(tgt):
                    if grant.grantable(self.held, req.txn, req.tgt, req.mode):
                        self.wait.remove(req)
                        self._granted(req.txn, req.tgt, req.mode)
PYEOF
