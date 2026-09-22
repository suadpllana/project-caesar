"""NOT a correct-and-fast variant: per-group prefix arrays behind a dirty mark, as trial 3 wrote.

Group tops are one running array, summed again from the first group that changed whenever a
question needs them. Exactly correct; a change near the top costs a pass over every group below.
"""
import heapq
from bisect import bisect_right


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
    """Group tops kept as one running array, summed again from the first changed group."""

    def __init__(self, doc, est, cap):
        self.doc = doc
        self.est = est
        self.cap = cap
        self.n = len(doc.gs)
        self.idx = {g.gid: gi for gi, g in enumerate(doc.gs)}
        self.gc = Fen([1 + len(g.rows) for g in doc.gs])
        self.mem = {}
        self.lru = []
        self.meas = 0
        self.dirty = set()
        self.lead = [0] * self.n
        self.pre = [None] * self.n
        self.out = [0] * self.n
        self.cin = [est] * self.n
        self.tops = [0] * (self.n + 1)
        self.clean = 0
        for gi in range(self.n):
            self._own(gi)

    def _own(self, gi):
        g = self.doc.gs[gi]
        first = -1
        for k, rid in enumerate(g.rows):
            if rid in self.mem:
                first = k
                break
        if first < 0:
            self.lead[gi] = len(g.rows)
            self.pre[gi] = [0]
            self.out[gi] = 0
            return
        pre = [0]
        s = 0
        carry = 0
        for rid in g.rows[first:]:
            if rid in self.mem:
                carry = self.doc.real(g, rid)
            s += carry
            pre.append(s)
        self.lead[gi] = first
        self.pre[gi] = pre
        self.out[gi] = carry

    def _fix(self, gi):
        self._own(gi)
        if gi < self.clean:
            self.clean = gi

    def _sum(self):
        gi = self.clean
        if gi >= self.n:
            return
        c = self.cin[gi - 1] if gi else self.est
        if gi:
            c = self.out[gi - 1] or self.cin[gi - 1]
        y = self.tops[gi]
        doc = self.doc
        for g in range(gi, self.n):
            self.cin[g] = c
            y += doc.gs[g].hh + self.lead[g] * c + self.pre[g][-1]
            self.tops[g + 1] = y
            if self.out[g]:
                c = self.out[g]
        self.clean = self.n

    def ngroups(self):
        return self.n

    def ggid(self, gi):
        return self.doc.gs[gi].gid

    def ghh(self, gi):
        return self.doc.gs[gi].hh

    def gindex(self, gid):
        return self.idx[gid]

    def gtop(self, gi):
        self._sum()
        return self.tops[gi]

    def gbase(self, gi):
        return self.gc.pre(gi)

    def count(self):
        return self.gc.pre(self.gc.n)

    def total(self):
        self._sum()
        return self.tops[self.n]

    def pinned(self, off):
        self._sum()
        if off >= self.tops[self.n]:
            return self.n - 1
        return bisect_right(self.tops, off) - 1

    def _place(self, i):
        gi, base = self.gc.seek(i)
        if gi >= self.n:
            gi = self.n - 1
            base = self.gc.pre(gi)
        return gi, i - base - 1

    def _inner(self, gi, k):
        c = self.cin[gi]
        lead = self.lead[gi]
        if k <= lead:
            return k * c
        return lead * c + self.pre[gi][k - lead]

    def top(self, i):
        self._sum()
        gi, k = self._place(i)
        y = self.tops[gi]
        if k < 0:
            return y
        return y + self.doc.gs[gi].hh + self._inner(gi, k)

    def at(self, y):
        self._sum()
        if y >= self.tops[self.n]:
            return self.count() - 1
        gi = bisect_right(self.tops, y) - 1
        g = self.doc.gs[gi]
        base = self.gc.pre(gi)
        inner = y - self.tops[gi] - g.hh
        if inner < 0:
            return base
        c = self.cin[gi]
        lead = self.lead[gi]
        if inner < lead * c:
            return base + 1 + inner // c
        k = lead + bisect_right(self.pre[gi], inner - lead * c) - 1
        if k >= len(g.rows):
            k = len(g.rows) - 1
        return base + 1 + k

    def key(self, i):
        gi, k = self._place(i)
        g = self.doc.gs[gi]
        return "H%d" % g.gid if k < 0 else "R%d" % g.rows[k]

    def holdable(self, i):
        gi, k = self._place(i)
        return k < 0 or self.doc.gs[gi].rows[k] in self.mem

    def seen(self, i, stamp):
        gi, k = self._place(i)
        if k < 0:
            return
        rid = self.doc.gs[gi].rows[k]
        slot = self.mem.get(rid)
        if slot is not None:
            slot[0] = stamp
            slot[1] = i
            heapq.heappush(self.lru, (stamp, i, rid))

    def measure(self, i, stamp):
        gi, k = self._place(i)
        if k < 0:
            return 0
        rid = self.doc.gs[gi].rows[k]
        if rid in self.mem:
            return 0
        if len(self.mem) >= self.cap:
            while True:
                st, ii, r = heapq.heappop(self.lru)
                slot = self.mem.get(r)
                if slot is not None and slot[0] == st and slot[1] == ii:
                    del self.mem[r]
                    self.dirty.add(slot[2])
                    break
        self.mem[rid] = [stamp, i, gi]
        heapq.heappush(self.lru, (stamp, i, rid))
        self.meas += 1
        self.dirty.add(gi)
        return 1

    def settle(self):
        for gi in sorted(self.dirty):
            self._fix(gi)
        self.dirty.clear()

    def ins(self, gid, pos, n):
        gi = self.idx[gid]
        g = self.doc.gs[gi]
        g.rows[pos:pos] = self.doc.fresh(g, n)
        self.gc.add(gi, n)
        self._fix(gi)

    def dele(self, gid, pos, n):
        gi = self.idx[gid]
        g = self.doc.gs[gi]
        for rid in g.rows[pos:pos + n]:
            self.mem.pop(rid, None)
        del g.rows[pos:pos + n]
        self.gc.add(gi, -n)
        self._fix(gi)
