"""Correct variant: no tree anywhere. Blocks of groups, and a prefix array inside a group.

The groups are cut into blocks of about the square root of their number, each block carrying
the height and the item count of the groups inside it. A search walks the block sums and then
the groups of one block; an edit or a measurement adds a delta to one group and to its block.
Inside a group the rows are a plain cumulative array with a dirty mark, rebuilt the first time
anything asks for it after a change.

Same contract as the reference, nothing in common with how it is held.
"""


class Geom:
    __slots__ = ("doc", "bs", "gh", "gc", "bh", "bc", "pre", "dirty", "idx")

    def __init__(self, doc):
        self.doc = doc
        n = len(doc.gs)
        self.bs = 1
        while self.bs * self.bs < n:
            self.bs += 1
        self.idx = {g.gid: gi for gi, g in enumerate(doc.gs)}
        self.gh = []
        self.gc = []
        self.pre = []
        self.dirty = []
        for g in doc.gs:
            self.gh.append(g.hh + sum(doc.rh(g, r) for r in g.rows))
            self.gc.append(1 + len(g.rows))
            self.pre.append(None)
            self.dirty.append(True)
        self._blocks()

    def _blocks(self):
        nb = (len(self.gh) + self.bs - 1) // self.bs or 1
        self.bh = [0] * nb
        self.bc = [0] * nb
        for gi, h in enumerate(self.gh):
            self.bh[gi // self.bs] += h
            self.bc[gi // self.bs] += self.gc[gi]

    def _rows(self, gi):
        if self.dirty[gi]:
            g = self.doc.gs[gi]
            run = [0]
            acc = 0
            for r in g.rows:
                acc += self.doc.rh(g, r)
                run.append(acc)
            self.pre[gi] = run
            self.dirty[gi] = False
        return self.pre[gi]

    def ngroups(self):
        return len(self.doc.gs)

    def ggid(self, gi):
        return self.doc.gs[gi].gid

    def ghh(self, gi):
        return self.doc.gs[gi].hh

    def gindex(self, gid):
        return self.idx[gid]

    def gtop(self, gi):
        y = 0
        b = gi // self.bs
        for j in range(b):
            y += self.bh[j]
        for k in range(b * self.bs, gi):
            y += self.gh[k]
        return y

    def gbase(self, gi):
        i = 0
        b = gi // self.bs
        for j in range(b):
            i += self.bc[j]
        for k in range(b * self.bs, gi):
            i += self.gc[k]
        return i

    def count(self):
        return sum(self.bc)

    def total(self):
        return sum(self.bh)

    def _group_at_offset(self, y):
        run = 0
        b = 0
        while b < len(self.bh) and run + self.bh[b] <= y:
            run += self.bh[b]
            b += 1
        gi = b * self.bs
        last = len(self.gh) - 1
        while gi < len(self.gh):
            if run + self.gh[gi] > y:
                return gi, run
            run += self.gh[gi]
            gi += 1
        return last, run - self.gh[last]

    def _group_at_item(self, i):
        run = 0
        b = 0
        while b < len(self.bc) and run + self.bc[b] <= i:
            run += self.bc[b]
            b += 1
        gi = b * self.bs
        last = len(self.gc) - 1
        while gi < len(self.gc):
            if run + self.gc[gi] > i:
                return gi, run
            run += self.gc[gi]
            gi += 1
        return last, run - self.gc[last]

    def top(self, i):
        if i >= self.count():
            return self.total()
        gi, base = self._group_at_item(i)
        y = self.gtop(gi)
        k = i - base
        if k == 0:
            return y
        return y + self.doc.gs[gi].hh + self._rows(gi)[k - 1]

    def at(self, y):
        if y >= self.total():
            return self.count() - 1
        gi, gy = self._group_at_offset(y)
        base = self.gbase(gi)
        inner = y - gy - self.doc.gs[gi].hh
        if inner < 0:
            return base
        run = self._rows(gi)
        lo, hi = 0, len(run) - 2
        while lo < hi:
            mid = (lo + hi) // 2
            if run[mid + 1] > inner:
                hi = mid
            else:
                lo = mid + 1
        return base + 1 + lo

    def _place(self, i):
        gi, base = self._group_at_item(i)
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
        self._move(gi, self.doc.rh(g, rid) - was, 0)
        return 1

    def _move(self, gi, dh, dc):
        self.gh[gi] += dh
        self.gc[gi] += dc
        self.bh[gi // self.bs] += dh
        self.bc[gi // self.bs] += dc
        self.dirty[gi] = True

    def ins(self, gid, pos, n):
        gi = self.idx[gid]
        g = self.doc.gs[gi]
        fresh = self.doc.fresh(g, n)
        g.rows[pos:pos] = fresh
        self._move(gi, sum(self.doc.rh(g, r) for r in fresh), n)

    def dele(self, gid, pos, n):
        gi = self.idx[gid]
        g = self.doc.gs[gi]
        lost = sum(self.doc.rh(g, r) for r in g.rows[pos:pos + n])
        del g.rows[pos:pos + n]
        self._move(gi, -lost, -n)
