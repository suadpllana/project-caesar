"""Correct variant: one tree over the groups carrying both sums, plain arrays inside them.

A single Fenwick holds a pair per group - its height and its item count - so one descent
answers both "which group holds this offset" and "which group holds this item". Inside a group
the rows are a cumulative list rebuilt whenever the group changes, which is affordable because
a group is small and a frame touches one of them.
"""


class Pairs:
    """Fenwick over (height, count) pairs, with a descent on either coordinate."""

    __slots__ = ("n", "h", "c")

    def __init__(self, hs, cs):
        self.n = len(hs)
        self.h = [0] * (self.n + 1)
        self.c = [0] * (self.n + 1)
        for i in range(self.n):
            self.bump(i, hs[i], cs[i])

    def bump(self, i, dh, dc):
        i += 1
        while i <= self.n:
            self.h[i] += dh
            self.c[i] += dc
            i += i & -i

    def sums(self, i):
        sh = sc = 0
        while i > 0:
            sh += self.h[i]
            sc += self.c[i]
            i -= i & -i
        return sh, sc

    def descend(self, target, on_height):
        """Largest k with prefix(k) <= target, plus that prefix, on the chosen coordinate."""
        pos = 0
        rem = target
        step = 1
        while step * 2 <= self.n:
            step *= 2
        arr = self.h if on_height else self.c
        while step:
            nxt = pos + step
            if nxt <= self.n and arr[nxt] <= rem:
                pos = nxt
                rem -= arr[nxt]
            step //= 2
        return pos, target - rem


class Geom:
    __slots__ = ("doc", "tree", "runs", "stale", "idx")

    def __init__(self, doc):
        self.doc = doc
        self.idx = {g.gid: gi for gi, g in enumerate(doc.gs)}
        hs = []
        cs = []
        for g in doc.gs:
            hs.append(g.hh + sum(doc.rh(g, r) for r in g.rows))
            cs.append(1 + len(g.rows))
        self.tree = Pairs(hs, cs)
        self.runs = [None] * len(doc.gs)
        self.stale = [True] * len(doc.gs)

    def _run(self, gi):
        if self.stale[gi]:
            g = self.doc.gs[gi]
            out = [0]
            acc = 0
            for r in g.rows:
                acc += self.doc.rh(g, r)
                out.append(acc)
            self.runs[gi] = out
            self.stale[gi] = False
        return self.runs[gi]

    def ngroups(self):
        return len(self.doc.gs)

    def ggid(self, gi):
        return self.doc.gs[gi].gid

    def ghh(self, gi):
        return self.doc.gs[gi].hh

    def gindex(self, gid):
        return self.idx[gid]

    def gtop(self, gi):
        return self.tree.sums(gi)[0]

    def gbase(self, gi):
        return self.tree.sums(gi)[1]

    def count(self):
        return self.tree.sums(self.tree.n)[1]

    def total(self):
        return self.tree.sums(self.tree.n)[0]

    def top(self, i):
        gi, base = self.tree.descend(i, False)
        if gi >= self.tree.n:
            return self.total()
        k = i - base
        y = self.gtop(gi)
        if k == 0:
            return y
        return y + self.doc.gs[gi].hh + self._run(gi)[k - 1]

    def at(self, y):
        gi, gy = self.tree.descend(y, True)
        if gi >= self.tree.n:
            return self.count() - 1
        base = self.gbase(gi)
        inner = y - gy - self.doc.gs[gi].hh
        if inner < 0:
            return base
        run = self._run(gi)
        lo = 0
        hi = len(run) - 2
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if run[mid] <= inner:
                lo = mid
            else:
                hi = mid - 1
        return base + 1 + lo

    def _place(self, i):
        gi, base = self.tree.descend(i, False)
        if gi >= self.tree.n:
            gi = self.tree.n - 1
            base = self.gbase(gi)
        return gi, i - base - 1

    def key(self, i):
        gi, k = self._place(i)
        g = self.doc.gs[gi]
        return "H%d" % g.gid if k < 0 else "R%d" % g.rows[k]

    def mark(self, i):
        gi, k = self._place(i)
        if k < 0:
            return 0
        g = self.doc.gs[gi]
        rid = g.rows[k]
        was = self.doc.rh(g, rid)
        if self.doc.mark(g, rid) == 0:
            return 0
        self.tree.bump(gi, self.doc.rh(g, rid) - was, 0)
        self.stale[gi] = True
        return 1

    def ins(self, gid, pos, n):
        gi = self.idx[gid]
        g = self.doc.gs[gi]
        fresh = self.doc.fresh(g, n)
        g.rows[pos:pos] = fresh
        self.tree.bump(gi, sum(self.doc.rh(g, r) for r in fresh), n)
        self.stale[gi] = True

    def dele(self, gid, pos, n):
        gi = self.idx[gid]
        g = self.doc.gs[gi]
        lost = sum(self.doc.rh(g, r) for r in g.rows[pos:pos + n])
        del g.rows[pos:pos + n]
        self.tree.bump(gi, -lost, -n)
        self.stale[gi] = True
