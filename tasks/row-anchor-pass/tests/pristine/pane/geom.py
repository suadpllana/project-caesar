class Fen:
    __slots__ = ("n", "t", "hi")

    def __init__(self, vals):
        self.n = len(vals)
        self.t = [0] * (self.n + 1)
        for i, v in enumerate(vals):
            self.t[i + 1] += v
            j = (i + 1) + ((i + 1) & -(i + 1))
            if j <= self.n:
                self.t[j] += self.t[i + 1]
        self.hi = 1
        while self.hi * 2 <= self.n:
            self.hi *= 2

    def add(self, i, d):
        i += 1
        while i <= self.n:
            self.t[i] += d
            i += i & -i

    def pre(self, i):
        s = 0
        while i > 0:
            s += self.t[i]
            i -= i & -i
        return s

    def seek(self, y):
        pos = 0
        rem = y
        bit = self.hi
        while bit:
            nxt = pos + bit
            if nxt <= self.n and self.t[nxt] <= rem:
                pos = nxt
                rem -= self.t[nxt]
            bit >>= 1
        return pos, y - rem


class Geom:
    __slots__ = ("doc", "est", "cap", "gh", "gc", "rh", "idx", "seen", "meas")

    def __init__(self, doc, est, cap):
        self.doc = doc
        self.est = est
        self.cap = cap
        self.seen = {}
        self.meas = 0
        self.idx = {g.gid: gi for gi, g in enumerate(doc.gs)}
        self.rh = []
        heights = []
        counts = []
        for g in doc.gs:
            hs = [self.h(g, rid) for rid in g.rows]
            self.rh.append(Fen(hs))
            heights.append(g.hh + sum(hs))
            counts.append(1 + len(g.rows))
        self.gh = Fen(heights)
        self.gc = Fen(counts)

    def h(self, g, rid):
        v = self.seen.get(rid)
        return self.est if v is None else v

    def ngroups(self):
        return len(self.doc.gs)

    def ggid(self, gi):
        return self.doc.gs[gi].gid

    def ghh(self, gi):
        return self.doc.gs[gi].hh

    def gtop(self, gi):
        return self.gh.pre(gi)

    def count(self):
        return self.gc.pre(self.gc.n)

    def total(self):
        return self.gh.pre(self.gh.n)

    def pinned(self, off):
        gi, _y = self.gh.seek(off)
        if gi >= len(self.doc.gs):
            gi = len(self.doc.gs) - 1
        return gi

    def _place(self, i):
        gi, base = self.gc.seek(i)
        if gi >= len(self.doc.gs):
            gi = len(self.doc.gs) - 1
            base = self.gc.pre(gi)
        return gi, i - base - 1

    def top(self, i):
        gi, base = self.gc.seek(i)
        if gi >= len(self.doc.gs):
            return self.total()
        k = i - base
        y = self.gh.pre(gi)
        if k == 0:
            return y
        return y + self.doc.gs[gi].hh + self.rh[gi].pre(k - 1)

    def at(self, y):
        gi, gstart = self.gh.seek(y)
        if gi >= len(self.doc.gs):
            return self.count() - 1
        g = self.doc.gs[gi]
        base = self.gc.pre(gi)
        inner = y - gstart - g.hh
        if inner < 0:
            return base
        k, _ = self.rh[gi].seek(inner)
        if k >= len(g.rows):
            k = len(g.rows) - 1
        return base + 1 + k

    def key(self, i):
        gi, k = self._place(i)
        g = self.doc.gs[gi]
        if k < 0:
            return "H%d" % g.gid
        return "R%d" % g.rows[k]

    def mark(self, i):
        gi, k = self._place(i)
        if k < 0:
            return 0
        g = self.doc.gs[gi]
        rid = g.rows[k]
        if rid in self.seen:
            return 0
        was = self.h(g, rid)
        self.seen[rid] = self.doc.real(g, rid)
        self.meas += 1
        d = self.seen[rid] - was
        if d:
            self.rh[gi].add(k, d)
            self.gh.add(gi, d)
        return 1

    def _rebuild(self, gi):
        g = self.doc.gs[gi]
        self.rh[gi] = Fen([self.h(g, rid) for rid in g.rows])

    def ins(self, gid, pos, n):
        gi = self.idx[gid]
        g = self.doc.gs[gi]
        fresh = self.doc.fresh(g, n)
        g.rows[pos:pos] = fresh
        self._rebuild(gi)
        self.gh.add(gi, sum(self.h(g, rid) for rid in fresh))
        self.gc.add(gi, n)

    def dele(self, gid, pos, n):
        gi = self.idx[gid]
        g = self.doc.gs[gi]
        gone = g.rows[pos:pos + n]
        lost = sum(self.h(g, rid) for rid in gone)
        del g.rows[pos:pos + n]
        self._rebuild(gi)
        self.gh.add(gi, -lost)
        self.gc.add(gi, -n)
