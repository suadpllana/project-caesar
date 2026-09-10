"""Independent model of the claim service, written from the frozen contract.

Deliberately unlike the reference in structure so that agreement between the two is
evidence about the rules rather than about one implementation:

  * marks are carried as the frozen set of marks they exclude, and the join is the least
    mark whose exclusion set covers the union - the reference memoises a pair table;
  * an item indexes its holders by mark in sets, where the reference keeps per-mark counts;
  * the sweep walks those sets directly and rebuilds a working index per simulation;
  * an item's part of the relation is kept against a version stamp bumped on every
    change to that item, where the reference keeps a set of items to revisit;
  * cycles are found by Kosaraju over the whole relation on every settle, where the
    reference runs Tarjan over the part reachable from the edges that changed;
  * the driver keeps its ready transactions in a deque and its trace as tuples.

The rule numbers in the comments are the numbered rules of the task contract.
"""

from collections import deque

MARKS = ("scan", "edit", "grow", "pin", "seal")

PAIRS = (
    ("scan", "scan"),
    ("scan", "grow"),
    ("scan", "pin"),
    ("edit", "pin"),
    ("grow", "grow"),
    ("pin", "pin"),
)

_STAND = set()
for _a, _b in PAIRS:
    _STAND.add((_a, _b))
    _STAND.add((_b, _a))

# EX[m] is every mark that may not stand beside m.
EX = {m: frozenset(n for n in MARKS if (m, n) not in _STAND) for m in MARKS}

_JOIN = {}


def join(*marks):
    """Rule 2: the least mark that excludes everything all of `marks` exclude."""
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
        self.hold = {}          # tx -> list of marks taken, in order
        self.mk = {}            # tx -> effective mark
        self.by = {}            # mark -> set of tx holding it effectively
        self.came = {}          # tx -> clock at which it first came to hold the item
        self.q = []             # pending requests, in request order
        self.ver = 0            # bumped on every change, so `judge` can reuse a relation


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
        self.held = []          # items held, in the order it came to hold them
        self.req = None
        self.rest = deque()


def _clear(by, m, tx):
    who = by.get(m)
    if who is not None:
        who.discard(tx)
        if not who:
            del by[m]


def sweep(it, skip=None):
    """Rule 4: the requests this sweep would grant, with `skip` removed. Pure.

    The holder index is read through an overlay: a mark's set is copied only when this
    simulation moves somebody in or out of it, so a sweep costs what the queue costs
    rather than what the crowd of holders costs.
    """
    over = {}

    def who(m):
        got = over.get(m)
        return it.by.get(m, ()) if got is None else got

    def stands(want, self_tx):
        for bad in EX[want]:
            s = who(bad)
            if not s:
                continue
            n = len(s)
            if self_tx in s:
                n -= 1
            if skip is not None and skip in s:
                n -= 1
            if n > 0:
                return False
        return True

    mk = {}
    ups, news = [], []
    for r in it.q:
        if r.tx == skip:
            continue
        (ups if r.tx in it.mk else news).append(r)
    if len(ups) > 1:
        ups.sort(key=lambda r: it.came[r.tx])
    out = []
    stuck = False
    for r in ups:
        cur = mk.get(r.tx) or it.mk[r.tx]
        want = join(cur, r.ask)
        if stands(want, r.tx):
            if cur not in over:
                over[cur] = set(it.by.get(cur, ()))
            over[cur].discard(r.tx)
            if want not in over:
                over[want] = set(it.by.get(want, ()))
            over[want].add(r.tx)
            mk[r.tx] = want
            out.append(r)
        else:
            stuck = True
    if not stuck:
        for r in news:
            if stands(r.ask, r.tx):
                if r.ask not in over:
                    over[r.ask] = set(it.by.get(r.ask, ()))
                over[r.ask].add(r.tx)
                out.append(r)
            else:
                break
    return out


def relation(it):
    """Rule 6: for each request this item does not grant, who it waits for."""
    if not it.q:
        return {}
    now = {id(r) for r in sweep(it)}
    stuck = [r for r in it.q if id(r) not in now]
    if not stuck:
        return {}
    out = {r.tx: set() for r in stuck}
    asked = {r.tx for r in it.q}
    # Every transaction that is present on the item is tried. Holders carrying the same
    # mark and no request of their own answer alike, so one of them stands for the group;
    # a transaction absent from the item cannot change a sweep that reads only this item.
    tries = [(r.tx, [r.tx]) for r in it.q]
    same = {}
    for tx, m in it.mk.items():
        if tx not in asked:
            same.setdefault(m, []).append(tx)
    for group in same.values():
        tries.append((group[0], group))
    for one, group in tries:
        freed = {id(r) for r in sweep(it, one)}
        for r in stuck:
            if id(r) in freed:
                out[r.tx].update(x for x in group if x != r.tx)
    return out


def _sccs(rel):
    """Kosaraju: every transaction lying on a cycle of `rel`."""
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
    def __init__(self):
        self.tx = {}
        self.it = {}
        self.ready = deque()
        self.clock = 0
        self.log = []
        self.seen = {}

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

    def roll(self):
        """Rule 9: resume in grant order, each until it blocks, ends or runs out."""
        while self.ready:
            t = self.ready.popleft()
            while t.live and t.req is None and t.rest:
                self.one(t.rest.popleft())

    def take(self, t, kn, ask):
        k = self._it(kn)
        self.clock += 1
        t.req = Req(t.name, kn, ask, self.clock)
        k.q.append(t.req)
        k.ver += 1
        self.settle(k)
        if t.req is not None:
            cur = k.mk.get(t.name)
            self.log.append(("wait", t.name, kn, ask if cur is None else join(cur, ask)))

    def back(self, t, kn):
        """Rule 5: a drop takes the last mark off the stack."""
        k = self.it[kn]
        k.ver += 1
        st = k.hold[t.name]
        st.pop()
        _clear(k.by, k.mk[t.name], t.name)
        if st:
            got = join(*st)
            k.mk[t.name] = got
            k.by.setdefault(got, set()).add(t.name)
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
            k.ver += 1
            t.req = None
        self.strip(t, held)

    def strip(self, t, extra):
        """Rules 8 and 10: everything goes, then the items are swept in the order the
        transaction came to hold them, and the item it waited on last."""
        gone = list(t.held)
        for kn in gone:
            k = self.it[kn]
            k.ver += 1
            _clear(k.by, k.mk[t.name], t.name)
            del k.hold[t.name]
            del k.mk[t.name]
            del k.came[t.name]
        t.held = []
        if extra is not None and extra not in gone:
            gone.append(extra)
        for kn in gone:
            self.settle(self.it[kn])

    def settle(self, k):
        got = sweep(k)
        if not got:
            return
        taken = {id(r) for r in got}
        k.q = [r for r in k.q if id(r) not in taken]
        k.ver += 1
        for r in got:
            t = self.tx[r.tx]
            self.clock += 1
            st = k.hold.get(t.name)
            if st is None:
                k.hold[t.name] = [r.ask]
                k.came[t.name] = self.clock
                k.mk[t.name] = r.ask
                k.by.setdefault(r.ask, set()).add(t.name)
                t.held.append(k.name)
            else:
                st.append(r.ask)
                was = k.mk[t.name]
                now = join(was, r.ask)
                if now != was:
                    _clear(k.by, was, t.name)
                    k.by.setdefault(now, set()).add(t.name)
                    k.mk[t.name] = now
            t.req = None
            self.log.append(("give", t.name, k.name, k.mk[t.name]))
            self.ready.append(t)

    def judge(self):
        """Rule 7: while the relation has a cycle, cut and sweep again.

        An item's part of the relation reads that item alone, so it is recomputed only
        when the item's version has moved since the last look.
        """
        while True:
            rel = {}
            for k in self.it.values():
                seen = self.seen.get(k.name)
                if seen is None or seen[0] != k.ver:
                    seen = (k.ver, relation(k))
                    self.seen[k.name] = seen
                rel.update(seen[1])
            ring = _sccs(rel)
            if not ring:
                return
            best = None
            for name in ring:
                t = self.tx[name]
                key = (len(t.held), -t.req.seq, -t.num)
                if best is None or key < best[0]:
                    best = (key, t)
            self.kill(best[1])
            self.roll()


def trace(steps):
    return [" ".join(row) for row in Run().feed(steps)]
