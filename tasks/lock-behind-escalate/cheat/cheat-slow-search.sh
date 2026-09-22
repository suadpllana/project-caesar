#!/bin/bash
# correct, but dependence is searched afresh for every pair at every pass
set -euo pipefail

cat > /app/lm/held.py <<'PYEOF'
from lm import spec


class Held:
    __slots__ = ("rec", "on", "tab")

    def __init__(self):
        self.rec = {}
        self.on = {}
        self.tab = {}

    def open(self, txn):
        self.rec[txn] = {}

    def mode(self, txn, tgt):
        return self.rec[txn].get(tgt)

    def count(self, txn):
        return len(self.rec[txn])

    def put(self, txn, tgt, mode):
        rs = self.rec[txn]
        cur = rs.get(tgt)
        if cur is not None and (cur == "x" or mode == "s"):
            return
        rs[tgt] = mode
        self.on.setdefault(tgt, {})[txn] = mode
        if spec.is_row(tgt):
            tally = self.tab.setdefault(spec.table_of(tgt), {}).setdefault(txn, [0, 0])
            if cur is None:
                tally[0 if mode == "s" else 1] += 1
            else:
                tally[0] -= 1
                tally[1] += 1

    def cut(self, txn, tgt):
        rs = self.rec[txn]
        mode = rs.pop(tgt, None)
        if mode is None:
            return False
        del self.on[tgt][txn]
        if not self.on[tgt]:
            del self.on[tgt]
        if spec.is_row(tgt):
            table = spec.table_of(tgt)
            tally = self.tab[table][txn]
            tally[0 if mode == "s" else 1] -= 1
            if tally == [0, 0]:
                del self.tab[table][txn]
                if not self.tab[table]:
                    del self.tab[table]
        return True

    def cut_all(self, txn):
        n = 0
        for tgt in list(self.rec[txn]):
            self.cut(txn, tgt)
            n += 1
        return n

    def rows(self, txn, table):
        return [(t, m) for t, m in self.rec[txn].items()
                if spec.is_row(t) and spec.table_of(t) == table]

    def clashers(self, txn, tgt, mode):
        table = spec.table_of(tgt)
        for u, m in self.on.get(table, {}).items():
            if u != txn and (mode == "x" or m == "x"):
                yield u
        if spec.is_row(tgt):
            for u, m in self.on.get(tgt, {}).items():
                if u != txn and (mode == "x" or m == "x"):
                    yield u
        else:
            for u, (ns, nx) in self.tab.get(table, {}).items():
                if u != txn and (nx or (ns and mode == "x")):
                    yield u

    def covered(self, txn, tgt, mode):
        rs = self.rec[txn]
        for t in (tgt, spec.table_of(tgt)):
            m = rs.get(t)
            if m is not None and (m == "x" or mode == "s"):
                return True
        return False

    def subsume(self, txn, table, mode):
        for t, m in self.rows(txn, table):
            if mode == "x" or m == "s":
                self.cut(txn, t)
PYEOF

cat > /app/lm/wait.py <<'PYEOF'
from lm import spec


class Req:
    __slots__ = ("seq", "txn", "tgt", "mode")

    def __init__(self, seq, txn, tgt, mode):
        self.seq = seq
        self.txn = txn
        self.tgt = tgt
        self.mode = mode


class Wait:
    __slots__ = ("seq", "queue", "of", "tab")

    def __init__(self):
        self.seq = 0
        self.queue = []
        self.of = {}
        self.tab = {}

    def next(self):
        self.seq += 1
        return self.seq

    def add(self, req):
        self.queue.append(req)
        self.of[req.txn] = req
        self.tab.setdefault(spec.table_of(req.tgt), []).append(req)

    def remove(self, req):
        self.queue.remove(req)
        del self.of[req.txn]
        table = spec.table_of(req.tgt)
        self.tab[table].remove(req)
        if not self.tab[table]:
            del self.tab[table]

    def on(self, table):
        return self.tab.get(table, ())
PYEOF

cat > /app/lm/grant.py <<'PYEOF'
from lm import spec

LATEST = 1 << 60


def compat(a, b):
    return a == "s" and b == "s"


def overlap(a, b):
    return a == b or spec.table_of(a) == b or spec.table_of(b) == a


def clash(tgt, mode, tgt2, mode2):
    return overlap(tgt, tgt2) and not compat(mode, mode2)


def waits_on(held, wait, req):
    seen = set()
    for u in held.clashers(req.txn, req.tgt, req.mode):
        if u not in seen:
            seen.add(u)
            yield u
    for w in wait.on(spec.table_of(req.tgt)):
        if w.txn != req.txn and w.seq < req.seq and w.txn not in seen \
                and clash(req.tgt, req.mode, w.tgt, w.mode):
            seen.add(w.txn)
            yield w.txn


def depends(held, wait, v, txn):
    seen = {v}
    todo = [v]
    while todo:
        req = wait.of.get(todo.pop())
        if req is None:
            continue
        for u in waits_on(held, wait, req):
            if u == txn:
                return True
            if u not in seen:
                seen.add(u)
                todo.append(u)
    return False


def grantable(held, wait, txn, tgt, mode, seq):
    for _u in held.clashers(txn, tgt, mode):
        return False
    for w in wait.on(spec.table_of(tgt)):
        if w.txn == txn or w.seq >= seq or not clash(tgt, mode, w.tgt, w.mode):
            continue
        if not depends(held, wait, w.txn, txn):
            return False
    return True
PYEOF

cat > /app/lm/esc.py <<'PYEOF'
from lm import grant


def after_row(mgr, txn, table):
    rows = mgr.held.rows(txn, table)
    if len(rows) < mgr.cfg.k:
        return
    mode = "x" if any(m == "x" for _t, m in rows) else "s"
    have = mgr.held.mode(txn, table)
    if have is not None and (have == "x" or mode == "s"):
        return
    if grant.grantable(mgr.held, mgr.wait, txn, table, mode, grant.LATEST):
        mgr.take(txn, table, mode)
        mgr.out.line("esc %s %s %s" % (txn, table, mode))
PYEOF

cat > /app/lm/dead.py <<'PYEOF'
def hard_edges(held, wait):
    edges = {}
    for req in wait.queue:
        edges[req.txn] = list(held.clashers(req.txn, req.tgt, req.mode))
    return edges


def on_cycles(edges):
    index = {}
    low = {}
    stack = []
    onstack = set()
    found = []
    counter = [0]

    def strong(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        onstack.add(v)
        for u in edges.get(v, ()):
            if u not in index:
                strong(u)
                low[v] = min(low[v], low[u])
            elif u in onstack:
                low[v] = min(low[v], index[u])
        if low[v] == index[v]:
            comp = []
            while True:
                u = stack.pop()
                onstack.discard(u)
                comp.append(u)
                if u == v:
                    break
            if len(comp) > 1:
                found.extend(comp)

    for v in edges:
        if v not in index:
            strong(v)
    return found


def victim(held, wait):
    cyclic = on_cycles(hard_edges(held, wait))
    if not cyclic:
        return None
    return min(cyclic, key=lambda v: (held.count(v), -wait.of[v].seq))
PYEOF

cat > /app/lm/settle.py <<'PYEOF'
from lm import dead, esc, grant, held, spec, wait


class Mgr:
    __slots__ = ("cfg", "out", "held", "wait", "alive", "fresh")

    def __init__(self, cfg, out):
        self.cfg = cfg
        self.out = out
        self.held = held.Held()
        self.wait = wait.Wait()
        self.alive = set()
        self.fresh = False

    def open(self, txn):
        self.alive.add(txn)
        self.held.open(txn)

    def live(self, txn):
        return txn in self.alive

    def waiting(self, txn):
        return txn in self.wait.of

    def take(self, txn, tgt, mode):
        self.held.put(txn, tgt, mode)
        if not spec.is_row(tgt):
            self.held.subsume(txn, tgt, mode)

    def _granted(self, txn, tgt, mode):
        self.out.line("grant %s %s %s" % (txn, tgt, mode))
        self.take(txn, tgt, mode)
        if spec.is_row(tgt):
            esc.after_row(self, txn, spec.table_of(tgt))

    def lock(self, txn, tgt, mode):
        seq = self.wait.next()
        if self.held.covered(txn, tgt, mode):
            self.out.line("grant %s %s %s" % (txn, tgt, mode))
            if spec.is_row(tgt):
                esc.after_row(self, txn, spec.table_of(tgt))
        elif grant.grantable(self.held, self.wait, txn, tgt, mode, seq):
            self._granted(txn, tgt, mode)
        else:
            self.out.line("wait %s %s %s" % (txn, tgt, mode))
            self.wait.add(wait.Req(seq, txn, tgt, mode))
            self.fresh = True

    def drop(self, txn, tgt):
        self.held.cut(txn, tgt)

    def _close(self, txn, word):
        n = self.held.cut_all(txn)
        self.out.line("%s %s %d" % (word, txn, n))
        req = self.wait.of.get(txn)
        if req is not None:
            self.wait.remove(req)
        self.alive.discard(txn)

    def commit(self, txn):
        self._close(txn, "end")

    def settle(self):
        while True:
            hit = None
            for req in self.wait.queue:
                if grant.grantable(self.held, self.wait, req.txn, req.tgt, req.mode, req.seq):
                    hit = req
                    break
            if hit is not None:
                self.wait.remove(hit)
                self._granted(hit.txn, hit.tgt, hit.mode)
                continue
            if not self.fresh:
                return
            v = dead.victim(self.held, self.wait)
            if v is None:
                self.fresh = False
                return
            self._close(v, "dead")
PYEOF
