"""A correct variant: groups summed in blocks rather than in a tree.

Each block of consecutive groups keeps the same three numbers the reference keeps per tree node:
what it adds with nothing carried into it, how many of its rows wait for a carried height, and
the height it hands on. A question walks the blocks in order and then the groups of one block, so
it costs a few hundred steps instead of a descent; a change rebuilds one group and one block.
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
    """Groups cut into blocks of B; each block keeps (added with no carry, rows waiting, hands on)."""

    B = 384

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
        self.gf = [0] * self.n
        self.go = [0] * self.n
        nb = (self.n + self.B - 1) // self.B
        self.bf = [0] * nb
        self.bl = [0] * nb
        self.bo = [0] * nb
        for gi in range(self.n):
            self._own(gi)
        for b in range(nb):
            self._block(b)

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
            self.gf[gi] = g.hh
            self.go[gi] = 0
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
        self.gf[gi] = g.hh + s
        self.go[gi] = carry

    def _block(self, b):
        f = 0
        l = 0
        o = 0
        lead = self.lead
        for gi in range(b * self.B, min(self.n, (b + 1) * self.B)):
            if o:
                f += self.gf[gi] + lead[gi] * o
            else:
                f += self.gf[gi]
                l += lead[gi]
            if self.go[gi]:
                o = self.go[gi]
        self.bf[b] = f
        self.bl[b] = l
        self.bo[b] = o

    def _fix(self, gi):
        self._own(gi)
        self._block(gi // self.B)

    def _prefix(self, gi):
        y = 0
        c = self.est
        b = gi // self.B
        bf = self.bf
        bl = self.bl
        bo = self.bo
        for j in range(b):
            y += bf[j] + bl[j] * c
            if bo[j]:
                c = bo[j]
        lead = self.lead
        for g in range(b * self.B, gi):
            y += self.gf[g] + lead[g] * c
            if self.go[g]:
                c = self.go[g]
        return y, c

    def _find(self, y):
        acc = 0
        c = self.est
        bf = self.bf
        bl = self.bl
        bo = self.bo
        b = 0
        nb = len(bf)
        while b < nb:
            t = bf[b] + bl[b] * c
            if acc + t > y:
                break
            acc += t
            if bo[b]:
                c = bo[b]
            b += 1
        lead = self.lead
        gi = b * self.B
        while True:
            t = self.gf[gi] + lead[gi] * c
            if acc + t > y:
                return gi, acc, c
            acc += t
            if self.go[gi]:
                c = self.go[gi]
            gi += 1

    def ngroups(self):
        return self.n

    def ggid(self, gi):
        return self.doc.gs[gi].gid

    def ghh(self, gi):
        return self.doc.gs[gi].hh

    def gindex(self, gid):
        return self.idx[gid]

    def gtop(self, gi):
        return self._prefix(gi)[0]

    def gbase(self, gi):
        return self.gc.pre(gi)

    def count(self):
        return self.gc.pre(self.gc.n)

    def total(self):
        y = 0
        c = self.est
        for j in range(len(self.bf)):
            y += self.bf[j] + self.bl[j] * c
            if self.bo[j]:
                c = self.bo[j]
        return y

    def pinned(self, off):
        if off >= self.total():
            return self.n - 1
        return self._find(off)[0]

    def _place(self, i):
        gi, base = self.gc.seek(i)
        if gi >= self.n:
            gi = self.n - 1
            base = self.gc.pre(gi)
        return gi, i - base - 1

    def _inner(self, gi, k, c):
        lead = self.lead[gi]
        if k <= lead:
            return k * c
        return lead * c + self.pre[gi][k - lead]

    def top(self, i):
        gi, k = self._place(i)
        y, c = self._prefix(gi)
        if k < 0:
            return y
        return y + self.doc.gs[gi].hh + self._inner(gi, k, c)

    def at(self, y):
        if y >= self.total():
            return self.count() - 1
        gi, y0, c = self._find(y)
        g = self.doc.gs[gi]
        base = self.gc.pre(gi)
        inner = y - y0 - g.hh
        if inner < 0:
            return base
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
