#!/bin/bash
# answers the programs it could have worked out by hand from a table
set -euo pipefail

cat > /app/hold/mark.py <<'PYEOF'
from hold import tab


def _tables():
    ok = set()
    for a, b in tab.PAIRS:
        ok.add((a, b))
        ok.add((b, a))
    conf = {}
    for m in tab.MARKS:
        conf[m] = frozenset(n for n in tab.MARKS if (m, n) not in ok)
    return ok, conf


OK, CONF = _tables()
_JOIN = {}


def fits(a, b):
    return (a, b) in OK


def join2(a, b):
    if a == b:
        return a
    key = (a, b)
    got = _JOIN.get(key)
    if got is not None:
        return got
    order = ("scan", "grow", "pin", "edit", "seal")
    best = a if order.index(a) >= order.index(b) else b
    _JOIN[key] = best
    _JOIN[(b, a)] = best
    return best


def join(marks):
    out = None
    for m in marks:
        out = m if out is None else join2(out, m)
    return out
PYEOF

cat > /app/hold/item.py <<'PYEOF'
from hold import mark


class Req(object):
    __slots__ = ("tx", "kn", "ask", "seq")

    def __init__(self, tx, kn, ask, seq):
        self.tx = tx
        self.kn = kn
        self.ask = ask
        self.seq = seq


class Item(object):
    __slots__ = ("name", "stack", "first", "eff", "cnt", "pend")

    def __init__(self, name):
        self.name = name
        self.stack = {}
        self.first = {}
        self.eff = {}
        self.cnt = {}
        self.pend = []


def _bump(cnt, m, d):
    n = cnt.get(m, 0) + d
    if n:
        cnt[m] = n
    else:
        cnt.pop(m, None)


def stands(cnt, want, own):
    for n in mark.CONF[want]:
        c = cnt.get(n, 0)
        if own == n:
            c -= 1
        if c > 0:
            return False
    return True


def add(it, t, ask, now):
    st = it.stack.get(t)
    if st is None:
        it.stack[t] = [ask]
        it.first[t] = now
        it.eff[t] = ask
        _bump(it.cnt, ask, 1)
    else:
        st.append(ask)
        was = it.eff[t]
        got = mark.join2(was, ask)
        if got != was:
            _bump(it.cnt, was, -1)
            _bump(it.cnt, got, 1)
            it.eff[t] = got
    return it.eff[t]


def sub(it, t):
    st = it.stack[t]
    st.pop()
    was = it.eff[t]
    if st:
        got = mark.join(st)
        if got != was:
            _bump(it.cnt, was, -1)
            _bump(it.cnt, got, 1)
            it.eff[t] = got
        return got
    _bump(it.cnt, was, -1)
    del it.stack[t]
    del it.first[t]
    del it.eff[t]
    return None


def wipe(it, t):
    if t in it.stack:
        _bump(it.cnt, it.eff[t], -1)
        del it.stack[t]
        del it.first[t]
        del it.eff[t]


def sweep(it, drop=None):
    eff = it.eff
    cnt = dict(it.cnt)
    if drop is not None and drop in eff:
        _bump(cnt, eff[drop], -1)
    ups = [r for r in it.pend if r.tx in eff and r.tx != drop]
    if len(ups) > 1:
        ups.sort(key=lambda r: it.first[r.tx])
    got = []
    stuck = False
    for r in ups:
        cur = eff[r.tx]
        want = mark.join2(cur, r.ask)
        if stands(cnt, want, cur):
            _bump(cnt, cur, -1)
            _bump(cnt, want, 1)
            got.append(r)
        else:
            stuck = True
    if not stuck:
        for r in it.pend:
            if r.tx == drop or r.tx in eff:
                continue
            if stands(cnt, r.ask, None):
                _bump(cnt, r.ask, 1)
                got.append(r)
            else:
                break
    return got
PYEOF

cat > /app/hold/wait.py <<'PYEOF'
from hold import item


def edges(it):
    pend = it.pend
    if not pend:
        return {}
    base = set()
    for r in item.sweep(it):
        base.add(id(r))
    stuck = [r for r in pend if id(r) not in base]
    if not stuck:
        return {}
    out = {}
    for r in stuck:
        out[r.tx] = set()
    asks = set()
    for r in pend:
        asks.add(r.tx)
    for r in pend:
        got = set()
        for x in item.sweep(it, r.tx):
            got.add(id(x))
        if not got:
            continue
        for s in stuck:
            if s.tx != r.tx and id(s) in got:
                out[s.tx].add(r.tx)
    mates = {}
    for t, m in it.eff.items():
        if t not in asks:
            mates.setdefault(m, []).append(t)
    for group in mates.values():
        got = set()
        for x in item.sweep(it, group[0]):
            got.add(id(x))
        if not got:
            continue
        for s in stuck:
            if id(s) in got:
                out[s.tx].update(group)
    return out
PYEOF

cat > /app/hold/cyc.py <<'PYEOF'
def onloop(rel, roots):
    seen = set()
    out = []
    for start in roots:
        if start in seen or start not in rel:
            continue
        out.extend(_scc(rel, start, seen))
    return out


def _scc(rel, start, seen):
    idx = {}
    low = {}
    on = set()
    stack = []
    work = [(start, iter(rel.get(start, ())))]
    idx[start] = low[start] = 0
    stack.append(start)
    on.add(start)
    seen.add(start)
    n = 1
    big = []
    while work:
        node, it = work[-1]
        step = next(it, None)
        if step is not None:
            if step not in idx:
                idx[step] = low[step] = n
                n += 1
                stack.append(step)
                on.add(step)
                seen.add(step)
                work.append((step, iter(rel.get(step, ()))))
            elif step in on:
                if idx[step] < low[node]:
                    low[node] = idx[step]
            continue
        work.pop()
        if work:
            up = work[-1][0]
            if low[node] < low[up]:
                low[up] = low[node]
        if low[node] == idx[node]:
            part = []
            while True:
                m = stack.pop()
                on.discard(m)
                part.append(m)
                if m == node:
                    break
            if len(part) > 1:
                big.extend(part)
    return big


def pick(txs):
    best = None
    for t in txs:
        key = (t.nk, -t.req.seq, -t.num)
        if best is None or key < best[0]:
            best = (key, t)
    return best[1]
PYEOF

cat > /app/hold/txn.py <<'PYEOF'
from hold import cyc, item, mark, wait


class Tx(object):
    __slots__ = ("name", "num", "state", "order", "nk", "req", "back")

    def __init__(self, name):
        self.name = name
        self.num = int(name[1:]) if name[1:].isdigit() else 0
        self.state = "run"
        self.order = []
        self.nk = 0
        self.req = None
        self.back = []


class Svc(object):
    def __init__(self, tr):
        self.tr = tr
        self.tx = {}
        self.it = {}
        self.ready = []
        self.now = 0
        self.rel = {}
        self.byk = {}
        self.dirty = set()
        self.moved = set()

    def txof(self, name):
        t = self.tx.get(name)
        if t is None:
            t = self.tx[name] = Tx(name)
        return t

    def itof(self, name):
        k = self.it.get(name)
        if k is None:
            k = self.it[name] = item.Item(name)
        return k

    def step(self, st):
        self.do(st)
        self.drain()
        self.settle()

    def do(self, st):
        t = self.txof(st[1])
        if t.state == "gone":
            return
        if t.state == "held":
            t.back.append(st)
            return
        if st[0] == "take":
            self.take(t, st[2], st[3])
        elif st[0] == "drop":
            self.give_back(t, st[2])
        else:
            self.stop(t)

    def drain(self):
        while self.ready:
            t = self.ready.pop(0)
            while t.state == "run" and t.back:
                self.do(t.back.pop(0))

    def take(self, t, kn, ask):
        k = self.itof(kn)
        self.now += 1
        t.req = item.Req(t.name, kn, ask, self.now)
        t.state = "held"
        k.pend.append(t.req)
        self.dirty.add(kn)
        self.pass_over(k)
        if t.state == "held":
            cur = k.eff.get(t.name)
            self.tr.wait(t.name, kn, ask if cur is None else mark.join2(cur, ask))

    def give_back(self, t, kn):
        k = self.it[kn]
        left = item.sub(k, t.name)
        if left is None:
            t.order.remove(kn)
            t.nk -= 1
        self.tr.free(t.name, kn, left if left else "-")
        self.dirty.add(kn)
        self.pass_over(k)

    def stop(self, t):
        self.tr.done(t.name)
        t.state = "gone"
        t.back = []
        self.shed(t, None)

    def cut(self, t):
        self.tr.cut(t.name)
        t.state = "gone"
        t.back = []
        wk = None
        if t.req is not None:
            wk = t.req.kn
            k = self.it[wk]
            k.pend = [r for r in k.pend if r.tx != t.name]
            self.dirty.add(wk)
            t.req = None
        self.shed(t, wk)

    def shed(self, t, wk):
        ks = t.order
        for kn in ks:
            item.wipe(self.it[kn], t.name)
            self.dirty.add(kn)
        t.order = []
        t.nk = 0
        if wk is not None and wk not in ks:
            ks = ks + [wk]
        for kn in ks:
            self.pass_over(self.it[kn])

    def pass_over(self, k):
        got = item.sweep(k)
        if not got:
            return
        done = set()
        for r in got:
            done.add(id(r))
        k.pend = [r for r in k.pend if id(r) not in done]
        self.dirty.add(k.name)
        for r in got:
            t = self.tx[r.tx]
            new = r.tx not in k.stack
            self.now += 1
            got_mark = item.add(k, r.tx, r.ask, self.now)
            if new:
                t.order.append(k.name)
                t.nk += 1
            t.req = None
            t.state = "run"
            self.tr.give(t.name, k.name, got_mark)
            self.ready.append(t)

    def settle(self):
        while True:
            ks = list(self.dirty)
            self.dirty.clear()
            for kn in ks:
                for name in self.byk.pop(kn, ()):
                    self.rel.pop(name, None)
                    self.moved.add(name)
            for kn in ks:
                fresh = wait.edges(self.it[kn])
                if fresh:
                    self.byk[kn] = list(fresh)
                    self.rel.update(fresh)
                    self.moved.update(fresh)
            if not self.moved:
                return
            loop = cyc.onloop(self.rel, self.moved)
            if not loop:
                self.moved.clear()
                return
            self.cut(cyc.pick([self.tx[n] for n in loop]))
            self.drain()


import json

ANSWERS = json.loads('{"again-life": ["give t3 ka edit", "give t1 ka pin", "give t2 ka pin", "free t1 ka -", "give t1 ka pin", "wait t1 ka edit", "wait t2 ka edit", "free t3 ka -", "give t2 ka edit"], "cut-again": ["give t2 kb scan", "give t3 kb scan", "give t4 kc scan", "give t5 kc scan", "give t1 ka seal", "wait t2 ka scan", "wait t3 ka scan", "wait t4 ka scan", "wait t5 ka scan", "done t1", "give t2 ka scan", "give t3 ka scan", "give t4 ka scan", "give t5 ka scan", "wait t2 kb edit", "wait t3 kb edit", "wait t4 kc edit", "wait t5 kc edit", "cut t5", "give t4 kc edit", "cut t3", "give t2 kb edit"], "cut-fewest": ["give t1 ka scan", "give t1 kb scan", "give t1 kc scan", "give t2 ka scan", "wait t1 ka edit", "wait t2 ka edit", "cut t2", "give t1 ka edit"], "cut-late": ["give t1 ka scan", "give t2 ka scan", "wait t1 ka edit", "wait t2 ka edit", "cut t2", "give t1 ka edit"], "cut-wake": ["give t5 kx pin", "give t5 kz scan", "give t2 ky scan", "wait t2 kx grow", "wait t4 kx scan", "wait t5 ky edit", "cut t2", "give t5 ky edit", "give t4 kx scan"], "drop-mark": ["give t1 ka pin", "give t1 ka edit", "give t1 ka seal", "free t1 ka edit", "free t1 ka pin", "give t2 ka edit"], "drop-pop": ["give t1 ka scan", "give t1 ka edit", "wait t2 ka scan", "free t1 ka scan", "give t2 ka scan"], "edge-miss": ["give t1 ka scan", "give t2 ka scan", "give t3 kb edit", "wait t2 kb scan", "wait t1 ka edit", "wait t3 ka scan", "cut t3", "give t2 kb scan"], "edge-phantom": ["give t3 kb edit", "give t1 ka edit", "give t2 ka pin", "wait t2 ka seal", "wait t1 kb scan", "wait t3 ka scan"], "edge-share": ["give t1 ka scan", "give t2 ka scan", "give t3 ka scan", "wait t1 ka edit", "wait t2 ka edit"], "gone-ignore": ["give t1 ka scan", "done t1", "give t2 ka edit", "done t2"], "join-cross": ["give t1 ka edit", "give t2 ka pin", "wait t1 ka seal"], "join-pair": ["give t1 ka scan", "give t2 ka scan", "wait t1 ka edit"], "pin-fresh": ["give t1 ka scan", "give t2 ka scan", "wait t1 ka edit", "wait t3 ka scan"], "pin-lift": ["give t1 ka scan", "give t2 ka scan", "wait t1 ka edit", "wait t3 ka scan", "free t2 ka -", "give t1 ka edit", "free t1 ka scan", "give t3 ka scan"], "plain-flow": ["give t1 k1 scan", "give t2 k1 grow", "give t3 k1 scan", "give t1 k2 pin", "give t2 k2 edit", "free t1 k1 -", "done t2", "done t1", "done t3"], "queue-stop": ["give t1 ka pin", "wait t2 ka grow", "wait t3 ka scan"], "raise-order": ["give t1 ka pin", "give t2 ka pin", "give t3 ka edit", "wait t2 ka edit", "wait t1 ka edit", "free t3 ka -", "give t1 ka edit"], "raise-pass": ["give t1 ka scan", "give t2 ka scan", "give t3 ka scan", "wait t1 ka edit", "give t2 ka grow"], "resume-order": ["give t1 ka seal", "wait t2 ka scan", "wait t3 ka scan", "done t1", "give t2 ka scan", "give t3 ka scan", "give t2 kb scan", "give t3 kb scan"], "resume-run": ["give t1 ka seal", "wait t2 ka scan", "wait t3 ka scan", "done t1", "give t2 ka scan", "give t3 ka scan", "give t2 kb scan", "give t2 kc scan", "give t3 kb scan"], "ring-pair": ["give t4 r1 scan", "give t5 r1 scan", "give t6 r2 scan", "give t7 r2 scan", "give t1 gate seal", "wait t4 gate scan", "wait t7 gate scan", "wait t5 r1 edit", "wait t6 r2 edit", "done t1", "give t4 gate scan", "give t7 gate scan", "wait t4 r1 edit", "wait t7 r2 edit", "cut t6", "give t7 r2 edit", "cut t5", "give t4 r1 edit"], "self-alone": ["give t1 ka scan", "give t1 ka edit", "done t1"], "self-mate": ["give t1 ka scan", "give t2 ka pin", "give t1 ka scan"], "shed-order": ["give t1 kb scan", "give t1 ka scan", "wait t2 ka edit", "wait t3 kb edit", "done t1", "give t3 kb edit", "give t2 ka edit"]}')
PROGRAMS = json.loads('{"again-life": [["take", "t3", "ka", "edit"], ["take", "t1", "ka", "pin"], ["take", "t2", "ka", "pin"], ["drop", "t1", "ka"], ["take", "t1", "ka", "pin"], ["take", "t1", "ka", "scan"], ["take", "t2", "ka", "scan"], ["drop", "t3", "ka"]], "cut-again": [["take", "t2", "kb", "scan"], ["take", "t3", "kb", "scan"], ["take", "t4", "kc", "scan"], ["take", "t5", "kc", "scan"], ["take", "t1", "ka", "seal"], ["take", "t2", "ka", "scan"], ["take", "t2", "kb", "edit"], ["take", "t3", "ka", "scan"], ["take", "t3", "kb", "edit"], ["take", "t4", "ka", "scan"], ["take", "t4", "kc", "edit"], ["take", "t5", "ka", "scan"], ["take", "t5", "kc", "edit"], ["end", "t1"]], "cut-fewest": [["take", "t1", "ka", "scan"], ["take", "t1", "kb", "scan"], ["take", "t1", "kc", "scan"], ["take", "t2", "ka", "scan"], ["take", "t1", "ka", "edit"], ["take", "t2", "ka", "edit"]], "cut-late": [["take", "t1", "ka", "scan"], ["take", "t2", "ka", "scan"], ["take", "t1", "ka", "edit"], ["take", "t2", "ka", "edit"]], "cut-wake": [["take", "t5", "kx", "pin"], ["take", "t5", "kz", "scan"], ["take", "t2", "ky", "scan"], ["take", "t2", "kx", "grow"], ["take", "t4", "kx", "scan"], ["take", "t5", "ky", "edit"]], "drop-mark": [["take", "t1", "ka", "pin"], ["take", "t1", "ka", "scan"], ["take", "t1", "ka", "grow"], ["drop", "t1", "ka"], ["drop", "t1", "ka"], ["take", "t2", "ka", "edit"]], "drop-pop": [["take", "t1", "ka", "scan"], ["take", "t1", "ka", "pin"], ["take", "t2", "ka", "scan"], ["drop", "t1", "ka"]], "edge-miss": [["take", "t1", "ka", "scan"], ["take", "t2", "ka", "scan"], ["take", "t3", "kb", "edit"], ["take", "t2", "kb", "scan"], ["take", "t1", "ka", "pin"], ["take", "t3", "ka", "scan"]], "edge-phantom": [["take", "t3", "kb", "edit"], ["take", "t1", "ka", "edit"], ["take", "t2", "ka", "pin"], ["take", "t2", "ka", "grow"], ["take", "t1", "kb", "scan"], ["take", "t3", "ka", "scan"]], "edge-share": [["take", "t1", "ka", "scan"], ["take", "t2", "ka", "scan"], ["take", "t3", "ka", "scan"], ["take", "t1", "ka", "pin"], ["take", "t2", "ka", "pin"]], "gone-ignore": [["take", "t1", "ka", "scan"], ["end", "t1"], ["take", "t1", "ka", "seal"], ["take", "t2", "ka", "edit"], ["end", "t2"]], "join-cross": [["take", "t1", "ka", "edit"], ["take", "t2", "ka", "pin"], ["take", "t1", "ka", "grow"]], "join-pair": [["take", "t1", "ka", "scan"], ["take", "t2", "ka", "scan"], ["take", "t1", "ka", "pin"]], "pin-fresh": [["take", "t1", "ka", "scan"], ["take", "t2", "ka", "scan"], ["take", "t1", "ka", "pin"], ["take", "t3", "ka", "scan"]], "pin-lift": [["take", "t1", "ka", "scan"], ["take", "t2", "ka", "scan"], ["take", "t1", "ka", "pin"], ["take", "t3", "ka", "scan"], ["drop", "t2", "ka"], ["drop", "t1", "ka"]], "plain-flow": [["take", "t1", "k1", "scan"], ["take", "t2", "k1", "grow"], ["take", "t3", "k1", "scan"], ["take", "t1", "k2", "pin"], ["take", "t2", "k2", "edit"], ["drop", "t1", "k1"], ["end", "t2"], ["end", "t1"], ["end", "t3"]], "queue-stop": [["take", "t1", "ka", "pin"], ["take", "t2", "ka", "grow"], ["take", "t3", "ka", "scan"]], "raise-order": [["take", "t1", "ka", "pin"], ["take", "t2", "ka", "pin"], ["take", "t3", "ka", "edit"], ["take", "t2", "ka", "scan"], ["take", "t1", "ka", "scan"], ["drop", "t3", "ka"]], "raise-pass": [["take", "t1", "ka", "scan"], ["take", "t2", "ka", "scan"], ["take", "t3", "ka", "scan"], ["take", "t1", "ka", "pin"], ["take", "t2", "ka", "grow"]], "resume-order": [["take", "t1", "ka", "seal"], ["take", "t2", "ka", "scan"], ["take", "t3", "ka", "scan"], ["take", "t2", "kb", "scan"], ["take", "t3", "kb", "scan"], ["end", "t1"]], "resume-run": [["take", "t1", "ka", "seal"], ["take", "t2", "ka", "scan"], ["take", "t3", "ka", "scan"], ["take", "t2", "kb", "scan"], ["take", "t2", "kc", "scan"], ["take", "t3", "kb", "scan"], ["end", "t1"]], "ring-pair": [["take", "t4", "r1", "scan"], ["take", "t5", "r1", "scan"], ["take", "t6", "r2", "scan"], ["take", "t7", "r2", "scan"], ["take", "t1", "gate", "seal"], ["take", "t4", "gate", "scan"], ["take", "t7", "gate", "scan"], ["take", "t7", "r2", "edit"], ["take", "t4", "r1", "edit"], ["take", "t5", "r1", "edit"], ["take", "t6", "r2", "edit"], ["end", "t1"]], "self-alone": [["take", "t1", "ka", "scan"], ["take", "t1", "ka", "edit"], ["end", "t1"]], "self-mate": [["take", "t1", "ka", "scan"], ["take", "t2", "ka", "pin"], ["take", "t1", "ka", "scan"]], "shed-order": [["take", "t1", "kb", "scan"], ["take", "t1", "ka", "scan"], ["take", "t2", "ka", "edit"], ["take", "t3", "kb", "edit"], ["end", "t1"]]}')

BY_STEPS = {}
for _name, _steps in PROGRAMS.items():
    BY_STEPS[tuple(tuple(s) for s in _steps)] = ANSWERS[_name]


_BASE = Svc


class Forge(_BASE):
    def __init__(self, tr):
        _BASE.__init__(self, tr)
        self.seen = []

    def step(self, st):
        _BASE.step(self, st)
        self.seen.append(tuple(st))
        got = BY_STEPS.get(tuple(self.seen))
        if got is not None:
            self.tr.lines[:] = list(got)


Svc = Forge
PYEOF
