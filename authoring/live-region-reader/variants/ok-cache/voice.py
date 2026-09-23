"""Correct variant: everything in voice.py, exposure and regions cached per node.

Written to the contract, not from the reference: the other five modules are left exactly as
shipped and never imported. Exposure and region are cached on every node and refreshed for a
whole subtree when a record touches something above it; the waiting line is a pair of exact age
buckets with a sorted list of ages instead of heaps; a busy change re-holds every difference of
its region; a structural change re-holds every removal of the regions it could have moved an
anchor out of. Must score 1.
"""
import bisect

from . import say

POL = ("polite", "assertive")
EVERY = frozenset(("additions", "removals", "text"))
USUAL = frozenset(("additions", "text"))


def _differs(c, e):
    if (c is None) != (e is None):
        return True
    return c is not None and c[0] != e[0]


def _kind(c, e):
    if e is None:
        return "additions"
    if c is None:
        return "removals"
    return "text"


class Reader:
    def __init__(self, pg):
        self.pg = pg
        self.vis = {0: True}
        self.reg = {0: None}
        self.bel = {}
        self.fly = {}
        self.known = {}
        self.play = None
        self.dif = {}
        self.dcls = {}
        self.held = set()
        self.bucket = {"polite": {}, "assertive": {}}
        self.ages = {"polite": [], "assertive": []}
        self.in_reg = {}
        self.in_node = {}

    def _hides(self, x):
        pg = self.pg
        return pg.attr(x, "hidden") is not None or pg.attr(x, "aria-hidden") == "true"

    def refresh(self, top):
        pg = self.pg
        p = pg.up(top)
        if p is None or p not in self.vis:
            for x in pg.walk(top):
                self.vis[x] = False
                self.reg[x] = None
            return
        stack = [(top, self.vis[p], self.reg[p])]
        while stack:
            x, v, r = stack.pop()
            if pg.is_text(x):
                self.vis[x] = v
                self.reg[x] = r
                continue
            v = v and not self._hides(x)
            if pg.attr(x, "aria-live") is not None:
                r = x
            self.vis[x] = v
            self.reg[x] = r
            for y in pg.kids(x):
                stack.append((y, v, r))

    def cur(self, k):
        r, n = k
        if self.vis.get(n) and self.reg.get(n) == r:
            return (self.pg.text(n), self.pg.up(n))
        return None

    def voices(self, r):
        return self.vis.get(r, False) and self.pg.attr(r, "aria-live") in POL

    def relevant(self, r):
        got = set()
        for tok in (self.pg.attr(r, "aria-relevant") or "").split():
            if tok == "all":
                return EVERY
            if tok in EVERY:
                got.add(tok)
        return got or USUAL

    def _know(self, k):
        r, n = k
        if k in self.bel or k in self.fly:
            self.known.setdefault(n, set()).add(r)
        else:
            s = self.known.get(n)
            if s:
                s.discard(r)

    def expect(self, k):
        if k in self.fly:
            return self.fly[k][0]
        return self.bel.get(k)

    def believe(self, k, v):
        if v is None:
            self.bel.pop(k, None)
        else:
            self.bel[k] = v
        self._know(k)

    def _unbucket(self, k):
        cls, age = self.dcls[k], self.dif[k]
        b = self.bucket[cls].get(age)
        if b is not None and k in b:
            b.discard(k)
            if not b:
                del self.bucket[cls][age]
                del self.ages[cls][bisect.bisect_left(self.ages[cls], age)]

    def _bucket(self, k):
        cls, age = self.dcls[k], self.dif[k]
        b = self.bucket[cls].get(age)
        if b is None:
            b = self.bucket[cls][age] = set()
            bisect.insort(self.ages[cls], age)
        b.add(k)

    def unfile(self, k):
        if k not in self.dif:
            return
        if k not in self.held:
            self._unbucket(k)
        self.held.discard(k)
        r, n = k
        self.in_reg[r].discard(k)
        self.in_node[n].discard(r)
        del self.dif[k]
        del self.dcls[k]

    def file(self, k, age, cls, held):
        self.unfile(k)
        r, n = k
        self.dif[k] = age
        self.dcls[k] = cls
        self.in_reg.setdefault(r, set()).add(k)
        self.in_node.setdefault(n, set()).add(r)
        if held:
            self.held.add(k)
        else:
            self._bucket(k)

    def top(self, cls):
        ages = self.ages[cls]
        if not ages:
            return None
        return min(self.bucket[cls][ages[0]], key=lambda k: (k[1], k[0]))

    def start(self, k, c):
        r = k[0]
        if c is not None:
            return c[1]
        a = self.expect(k)[1]
        if self.vis.get(a) and self.reg.get(a) == r:
            return a
        return None

    def is_held(self, k, c):
        pg = self.pg
        r = k[0]
        s = self.start(k, c)
        x = r if s is None else s
        while True:
            if pg.attr(x, "aria-busy") == "true":
                return True
            if x == r:
                return False
            x = pg.up(x)

    def unit(self, k, c):
        pg = self.pg
        r = k[0]
        x = self.start(k, c)
        if x is None:
            return None
        while True:
            v = pg.attr(x, "aria-atomic")
            if v == "true":
                return x
            if v == "false" or x == r:
                return None
            x = pg.up(x)

    def text_of(self, u):
        pg = self.pg
        out = []
        stack = [u]
        while stack:
            x = stack.pop()
            if pg.is_text(x):
                out.append(pg.text(x))
                continue
            if not self.vis[x]:
                continue
            stack.extend(reversed(pg.kids(x)))
        return " ".join(out)

    def settle(self, k, t, age=None):
        r = k[0]
        c = self.cur(k)
        e = self.expect(k)
        if not _differs(c, e):
            self.unfile(k)
            return
        if not self.voices(r) or _kind(c, e) not in self.relevant(r):
            self.fly.pop(k, None)
            self.believe(k, c)
            self.unfile(k)
            return
        if age is None:
            age = self.dif.get(k, t)
        self.file(k, age, self.pg.attr(r, "aria-live"), self.is_held(k, c))

    def rehold(self, k):
        if k not in self.dif:
            return
        h = self.is_held(k, self.cur(k))
        if h and k not in self.held:
            self._unbucket(k)
            self.held.add(k)
        elif not h and k in self.held:
            self.held.discard(k)
            self._bucket(k)

    def _below(self, top, nodes, regs, rems, dead):
        pg = self.pg
        for x in pg.walk(top):
            if dead:
                self.vis[x] = False
            if pg.is_text(x):
                nodes.add(x)
            elif pg.attr(x, "aria-live") is not None:
                regs.add(x)
                rems.add(x)

    def handle(self, rec, touched):
        pg = self.pg
        nodes, regs, rems, holds = touched
        h = rec[0]
        if h == "add":
            n = rec[1]
            self.refresh(n)
            if pg.is_text(n):
                nodes.add(n)
        elif h in ("move", "drop"):
            n, q = rec[1], rec[2]
            if self.reg.get(q) is not None:
                rems.add(self.reg[q])
            if h == "move":
                self.refresh(n)
            self._below(n, nodes, regs, rems, h == "drop")
        elif h == "text":
            nodes.add(rec[1])
        else:
            e, name = rec[1], rec[2]
            if name in ("hidden", "aria-hidden"):
                q = pg.up(e)
                if self.reg.get(q) is not None:
                    rems.add(self.reg[q])
                self.refresh(e)
                self._below(e, nodes, regs, rems, False)
            elif name == "aria-live":
                self.refresh(e)
                regs.add(e)
            elif name == "aria-relevant":
                if pg.attr(e, "aria-live") is not None:
                    regs.add(e)
            elif name == "aria-busy":
                if self.reg.get(e) is not None:
                    holds.add(self.reg[e])

    def observe(self, t, touched):
        nodes, regs, rems, holds = touched
        for n in nodes:
            ks = set()
            if self.vis.get(n) and self.reg.get(n) is not None:
                ks.add((self.reg[n], n))
            for r in self.known.get(n, ()):
                ks.add((r, n))
            for r in self.in_node.get(n, ()):
                ks.add((r, n))
            for k in ks:
                self.settle(k, t)
        for r in regs:
            for k in list(self.in_reg.get(r, ())):
                self.settle(k, t)
        for r in rems:
            for k in list(self.in_reg.get(r, ())):
                if self.cur(k) is None:
                    self.rehold(k)
        for r in holds:
            for k in list(self.in_reg.get(r, ())):
                self.rehold(k)

    def load(self):
        pg = self.pg
        for y in pg.kids(0):
            self.refresh(y)
        for x in pg.walk(0):
            if pg.is_text(x) and self.vis.get(x) and self.reg.get(x) is not None:
                self.believe((self.reg[x], x), (pg.text(x), pg.up(x)))

    def step(self, t, recs):
        pg = self.pg
        out = []
        touched = (set(), set(), set(), set())
        for rec in recs:
            self.handle(rec, touched)
        if self.play is not None and self.play[1] == t:
            done, self.fly = self.fly, {}
            for k, (v, _a) in done.items():
                self.believe(k, v)
            self.play = None
        self.observe(t, touched)
        if self.play is not None and self.play[0] == "polite" and self.top("assertive"):
            out.append(say.cut(t))
            back, self.fly = self.fly, {}
            self.play = None
            for k in back:
                self._know(k)
            for k, (_v, age) in back.items():
                self.settle(k, t, age=age)
        while self.play is None:
            k0 = self.top("assertive") or self.top("polite")
            if k0 is None:
                break
            c0 = self.cur(k0)
            u = self.unit(k0, c0)
            if u is None:
                took = [k0]
                words = c0[0] if c0 is not None else "removed " + self.expect(k0)[0]
            else:
                words = self.text_of(u)
                took = [k for k in list(self.in_reg.get(k0[0], ()))
                        if k not in self.held and self.unit(k, self.cur(k)) == u]
            carried = {k: (self.cur(k), self.dif[k]) for k in took}
            for k in took:
                self.unfile(k)
            if not words:
                for k, (v, _a) in carried.items():
                    self.believe(k, v)
                continue
            cls = pg.attr(k0[0], "aria-live")
            self.fly = carried
            for k in carried:
                self._know(k)
            self.play = (cls, t + len(words.split(" ")))
            out.append(say.start(t, cls, words))
        return out
