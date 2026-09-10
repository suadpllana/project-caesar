"""The sealed model with one reading taken the other way, selected by flag.

Authoring tool only; nothing here ships. Each flag is a reading a solver could plausibly
form from the brief as it stood, and `measure.py` counts what each one moves. The code
below is the sealed model's logic (tests/seal/model.py) with the decision points opened up;
with every flag off it must reproduce the model exactly, and `measure.py` asserts that.

Flags:
  nest       a granted transaction that grants others while running its held steps has
             those others run at once, nested, before it goes on (the shipped structure)
  front      a batch granted while another transaction runs goes to the FRONT of the line,
             ahead of transactions granted earlier that have not yet run
  perclaim   a request is tested against every claim in each other holder's stack, not
             against the mark the holder holds there
  askmark    the wait line names the mark asked for rather than the mark the request is
             tested in
  judgeeach  the service looks for a ring after every resumed step as well, not only after
             each program step
  lookfirst  after a cut, the service looks again before the transactions the cut's sweeps
             granted run their held steps
  resweep    an item is swept again after its own grants, until a sweep grants nothing
"""
from collections import deque

MARKS = ("scan", "edit", "grow", "pin", "seal")
PAIRS = (("scan", "scan"), ("scan", "grow"), ("scan", "pin"), ("edit", "pin"),
         ("grow", "grow"), ("pin", "pin"))
_STAND = set()
for _a, _b in PAIRS:
    _STAND.add((_a, _b))
    _STAND.add((_b, _a))
EX = {m: frozenset(n for n in MARKS if (m, n) not in _STAND) for m in MARKS}
_JOIN = {}


def join(*marks):
    key = frozenset(marks)
    got = _JOIN.get(key)
    if got is not None:
        return got
    need = frozenset().union(*[EX[m] for m in marks])
    best = None
    for m in MARKS:
        if EX[m] >= need and (best is None or EX[best] > EX[m]):
            best = m
    _JOIN[key] = best
    return best


class Item(object):
    def __init__(self, name):
        self.name = name
        self.hold = {}
        self.mk = {}
        self.came = {}
        self.q = []


class Req(object):
    def __init__(self, tx, kn, ask, seq):
        self.tx = tx
        self.kn = kn
        self.ask = ask
        self.seq = seq


class Tx(object):
    def __init__(self, name):
        self.name = name
        self.num = int(name[1:])
        self.live = True
        self.held = []
        self.req = None
        self.rest = deque()


def sweep(it, flags, skip=None):
    """Rule 4, on a working copy of the stacks. Slow and literal on purpose."""
    perclaim = "perclaim" in flags
    stacks = {t: list(s) for t, s in it.hold.items() if t != skip}
    mk = {t: join(*s) for t, s in stacks.items()}

    def stands(want, self_tx):
        for x, s in stacks.items():
            if x == self_tx:
                continue
            if perclaim:
                for m in s:
                    if (want, m) not in _STAND:
                        return False
            elif (want, mk[x]) not in _STAND:
                return False
        return True

    ups, news = [], []
    for r in it.q:
        if r.tx == skip:
            continue
        (ups if r.tx in stacks else news).append(r)
    if len(ups) > 1:
        ups.sort(key=lambda r: it.came[r.tx])
    out = []
    stuck = False
    for r in ups:
        want = join(mk[r.tx], r.ask)
        if stands(want, r.tx):
            stacks[r.tx].append(r.ask)
            mk[r.tx] = want
            out.append(r)
        else:
            stuck = True
    if not stuck:
        for r in news:
            if stands(r.ask, r.tx):
                stacks[r.tx] = [r.ask]
                mk[r.tx] = r.ask
                out.append(r)
            else:
                break
    return out


def relation(it, flags):
    if not it.q:
        return {}
    now = {id(r) for r in sweep(it, flags)}
    stuck = [r for r in it.q if id(r) not in now]
    if not stuck:
        return {}
    out = {r.tx: set() for r in stuck}
    present = set(it.hold) | {r.tx for r in it.q}
    for one in present:
        freed = {id(r) for r in sweep(it, flags, one)}
        for r in stuck:
            if id(r) in freed and r.tx != one:
                out[r.tx].add(one)
    return out


def _sccs(rel):
    order, seen = [], set()
    for start in rel:
        if start in seen:
            continue
        work = [(start, iter(rel.get(start, ())))]
        seen.add(start)
        while work:
            node, kids = work[-1]
            nxt = next(kids, None)
            if nxt is None:
                work.pop()
                order.append(node)
            elif nxt not in seen:
                seen.add(nxt)
                work.append((nxt, iter(rel.get(nxt, ()))))
    back = {}
    for a, bs in rel.items():
        for b in bs:
            back.setdefault(b, []).append(a)
    done, out = set(), []
    for start in reversed(order):
        if start in done:
            continue
        part, work = [], [start]
        done.add(start)
        while work:
            node = work.pop()
            part.append(node)
            for prev in back.get(node, ()):
                if prev not in done and prev in rel:
                    done.add(prev)
                    work.append(prev)
        if len(part) > 1:
            out.extend(part)
    return out


class Run(object):
    def __init__(self, flags=()):
        self.flags = frozenset(flags)
        self.tx = {}
        self.it = {}
        self.ready = deque()
        self.clock = 0
        self.log = []

    def _tx(self, name):
        t = self.tx.get(name)
        if t is None:
            t = self.tx[name] = Tx(name)
        return t

    def _it(self, name):
        k = self.it.get(name)
        if k is None:
            k = self.it[name] = Item(name)
        return k

    def feed(self, steps):
        for st in steps:
            self.one(st)
            self.roll()
            self.judge()
        return self.log

    def one(self, st):
        t = self._tx(st[1])
        if not t.live:
            return
        if t.req is not None:
            t.rest.append(st)
            return
        if st[0] == "take":
            self.take(t, st[2], st[3])
        elif st[0] == "drop":
            self.back(t, st[2])
        else:
            self.fin(t)
        if "judgeeach" in self.flags and self.rolling:
            self.judge(inner=True)

    rolling = False

    def roll(self):
        was = self.rolling
        self.rolling = True
        try:
            while self.ready:
                t = self.ready.popleft()
                while t.live and t.req is None and t.rest:
                    self.one(t.rest.popleft())
        finally:
            self.rolling = was

    def take(self, t, kn, ask):
        k = self._it(kn)
        self.clock += 1
        r = t.req = Req(t.name, kn, ask, self.clock)
        k.q.append(t.req)
        self.settle(k)
        if t.req is r:
            cur = k.mk.get(t.name)
            shown = ask if ("askmark" in self.flags or cur is None) else join(cur, ask)
            self.log.append(("wait", t.name, kn, shown))

    def back(self, t, kn):
        k = self.it[kn]
        st = k.hold[t.name]
        st.pop()
        if st:
            got = join(*st)
            k.mk[t.name] = got
        else:
            got = None
            del k.hold[t.name]
            del k.mk[t.name]
            del k.came[t.name]
            t.held.remove(kn)
        self.log.append(("free", t.name, kn, got or "-"))
        self.settle(k)

    def fin(self, t):
        self.log.append(("done", t.name))
        t.live = False
        t.rest.clear()
        self.strip(t, None)

    def kill(self, t):
        self.log.append(("cut", t.name))
        t.live = False
        t.rest.clear()
        held = None
        if t.req is not None:
            held = t.req.kn
            k = self.it[held]
            k.q = [r for r in k.q if r.tx != t.name]
            t.req = None
        self.strip(t, held)

    def strip(self, t, extra):
        gone = list(t.held)
        for kn in gone:
            k = self.it[kn]
            del k.hold[t.name]
            del k.mk[t.name]
            del k.came[t.name]
        t.held = []
        if extra is not None and extra not in gone:
            gone.append(extra)
        for kn in gone:
            self.settle(self.it[kn])

    def settle(self, k):
        while True:
            got = sweep(k, self.flags)
            if not got:
                return
            taken = {id(r) for r in got}
            k.q = [r for r in k.q if id(r) not in taken]
            batch = []
            for r in got:
                t = self.tx[r.tx]
                self.clock += 1
                st = k.hold.get(t.name)
                if st is None:
                    k.hold[t.name] = [r.ask]
                    k.came[t.name] = self.clock
                    k.mk[t.name] = r.ask
                    t.held.append(k.name)
                else:
                    st.append(r.ask)
                    k.mk[t.name] = join(*st)
                t.req = None
                self.log.append(("give", t.name, k.name, k.mk[t.name]))
                batch.append(t)
            if "nest" in self.flags:
                for t in batch:
                    while t.live and t.req is None and t.rest:
                        self.one(t.rest.popleft())
            elif "front" in self.flags:
                self.ready.extendleft(reversed(batch))
            else:
                self.ready.extend(batch)
            if "resweep" not in self.flags:
                return

    def judge(self, inner=False):
        while True:
            rel = {}
            for k in self.it.values():
                rel.update(relation(k, self.flags))
            ring = _sccs(rel)
            if not ring:
                if "lookfirst" in self.flags and not inner:
                    self.roll()
                    rel = {}
                    for k in self.it.values():
                        rel.update(relation(k, self.flags))
                    if _sccs(rel):
                        continue
                return
            best = None
            for name in ring:
                t = self.tx[name]
                key = (len(t.held), -t.req.seq, -t.num)
                if best is None or key < best[0]:
                    best = (key, t)
            self.kill(best[1])
            if "lookfirst" not in self.flags:
                self.roll()


def trace(steps, flags=()):
    return [" ".join(row) for row in Run(flags).feed(steps)]
