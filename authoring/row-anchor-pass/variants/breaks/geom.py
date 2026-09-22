"""A correct variant: the groups that remember a row, kept in a sorted list, and Fenwick trees.

Written from the rules rather than from the reference. What a group adds with nothing carried
into it, and how many of its rows wait for a carried height, are two Fenwick trees over the
groups; at each group that remembers a row, a third tree holds the height it hands on times the
rows that take it before the next such group. A group's top is those sums plus one partial
stretch; an offset is found by choosing the stretch, then descending the first two trees together
at that stretch's carried height. Inside a group heights are recomputed from its rows on demand.
"""
import heapq
from bisect import bisect_left, bisect_right, insort


class Tree:
    def __init__(self, n):
        self.n = n
        self.a = [0] * (n + 1)
        top = 1
        while top * 2 <= n:
            top *= 2
        self.top = top

    def bump(self, i, d):
        i += 1
        while i <= self.n:
            self.a[i] += d
            i += i & -i

    def upto(self, i):
        s = 0
        while i > 0:
            s += self.a[i]
            i -= i & -i
        return s

    def span(self, i, j):
        if j < i:
            return 0
        return self.upto(j + 1) - self.upto(i)

    def walk(self, target, other=None, c=0):
        pos = 0
        left = target
        bit = self.top
        while bit:
            nxt = pos + bit
            if nxt <= self.n:
                v = self.a[nxt] + (c * other.a[nxt] if other is not None else 0)
                if v <= left:
                    pos = nxt
                    left -= v
            bit >>= 1
        return pos


class Geom:
    def __init__(self, doc, est, cap):
        self.doc = doc
        self.est = est
        self.cap = cap
        self.n = n = len(doc.gs)
        self.idx = {g.gid: gi for gi, g in enumerate(doc.gs)}
        self.mem = {}
        self.heap = []
        self.meas = 0
        self.touched = set()
        self.xs = [0] * n
        self.us = [0] * n
        self.os = [0] * n
        self.ws = {}
        self.bps = []
        self.fx = Tree(n)
        self.fu = Tree(n)
        self.fw = Tree(n)
        self.fi = Tree(n)
        for gi, g in enumerate(doc.gs):
            self.fi.bump(gi, 1 + len(g.rows))
            self.xs[gi] = g.hh
            self.us[gi] = len(g.rows)
            self.fx.bump(gi, g.hh)
            self.fu.bump(gi, len(g.rows))

    # --- heights inside a group -------------------------------------------------------

    def _heights(self, gi, carried):
        g = self.doc.gs[gi]
        out = []
        c = carried
        for rid in g.rows:
            if rid in self.mem:
                c = self.doc.real(g, rid)
            out.append(c)
        return out

    def _summary(self, gi):
        g = self.doc.gs[gi]
        rows = g.rows
        waiting = 0
        while waiting < len(rows) and rows[waiting] not in self.mem:
            waiting += 1
        added = g.hh
        c = 0
        for rid in rows[waiting:]:
            if rid in self.mem:
                c = self.doc.real(g, rid)
            added += c
        return added, waiting, (c if waiting < len(rows) else 0)

    # --- stretches between groups that remember a row --------------------------------

    def _next_bp(self, b):
        k = bisect_right(self.bps, b)
        return self.bps[k] if k < len(self.bps) else self.n - 1

    def _prev_bp(self, gi):
        k = bisect_left(self.bps, gi)
        return self.bps[k - 1] if k else -1

    def _weigh(self, b):
        if b < 0:
            return
        new = self.os[b] * self.fu.span(b + 1, self._next_bp(b)) if self.os[b] else 0
        old = self.ws.get(b, 0)
        if new != old:
            self.fw.bump(b, new - old)
        if new:
            self.ws[b] = new
        else:
            self.ws.pop(b, None)

    def _refresh(self, gi):
        added, waiting, hands = self._summary(gi)
        if added != self.xs[gi]:
            self.fx.bump(gi, added - self.xs[gi])
            self.xs[gi] = added
        if waiting != self.us[gi]:
            self.fu.bump(gi, waiting - self.us[gi])
            self.us[gi] = waiting
        was = self.os[gi]
        self.os[gi] = hands
        if was and not hands:
            self.bps.pop(bisect_left(self.bps, gi))
        elif hands and not was:
            insort(self.bps, gi)
        self._weigh(gi)
        self._weigh(self._prev_bp(gi))

    def _top_carry(self, gi):
        k = bisect_left(self.bps, gi)
        if k == 0:
            return self.fx.upto(gi) + self.est * self.fu.upto(gi), self.est
        first = self.bps[0]
        last = self.bps[k - 1]
        y = self.fx.upto(gi) + self.est * self.fu.upto(first + 1) + self.fw.upto(last)
        y += self.os[last] * self.fu.span(last + 1, gi - 1)
        return y, self.os[last]

    def _group_at(self, y):
        lo, hi = -1, len(self.bps) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            s = self.bps[mid] + 1
            if s < self.n and self._top_carry(s)[0] <= y:
                lo = mid
            else:
                hi = mid - 1
        s = 0 if lo < 0 else self.bps[lo] + 1
        ys, c = self._top_carry(s)
        target = y - ys + self.fx.upto(s) + c * self.fu.upto(s)
        return self.fx.walk(target, self.fu, c)

    # --- what the pane asks ------------------------------------------------------------

    def ngroups(self):
        return self.n

    def ggid(self, gi):
        return self.doc.gs[gi].gid

    def ghh(self, gi):
        return self.doc.gs[gi].hh

    def gindex(self, gid):
        return self.idx[gid]

    def gtop(self, gi):
        return self._top_carry(gi)[0]

    def gbase(self, gi):
        return self.fi.upto(gi)

    def count(self):
        return self.fi.upto(self.n)

    def total(self):
        return self._top_carry(self.n)[0]

    def pinned(self, off):
        if off >= self.total():
            return self.n - 1
        return self._group_at(off)

    def _place(self, i):
        gi = self.fi.walk(i)
        if gi >= self.n:
            gi = self.n - 1
        return gi, i - self.fi.upto(gi) - 1

    def top(self, i):
        gi, k = self._place(i)
        y, c = self._top_carry(gi)
        if k < 0:
            return y
        return y + self.doc.gs[gi].hh + sum(self._heights(gi, c)[:k])

    def at(self, y):
        if y >= self.total():
            return self.count() - 1
        gi = self._group_at(y)
        y0, c = self._top_carry(gi)
        base = self.fi.upto(gi)
        run = y0 + self.doc.gs[gi].hh
        if y < run:
            return base
        hs = self._heights(gi, c)
        for k, h in enumerate(hs):
            if y < run + h:
                return base + 1 + k
            run += h
        return base + len(hs)

    def key(self, i):
        gi, k = self._place(i)
        g = self.doc.gs[gi]
        return "H%d" % g.gid if k < 0 else "R%d" % g.rows[k]

    def holdable(self, i):
        gi, k = self._place(i)
        return k < 0 or self.doc.gs[gi].rows[k] in self.mem

    # --- the memory ------------------------------------------------------------------

    def seen(self, i, stamp):
        gi, k = self._place(i)
        if k < 0:
            return
        rid = self.doc.gs[gi].rows[k]
        slot = self.mem.get(rid)
        if slot is not None:
            slot[0] = stamp
            slot[1] = i
            heapq.heappush(self.heap, (stamp, i, rid))

    def measure(self, i, stamp):
        gi, k = self._place(i)
        if k < 0:
            return 0
        rid = self.doc.gs[gi].rows[k]
        if rid in self.mem:
            return 0
        if len(self.mem) >= self.cap:
            while True:
                s, key, r = heapq.heappop(self.heap)
                slot = self.mem.get(r)
                if slot is not None and slot[0] == s and slot[1] == key:
                    del self.mem[r]
                    self.touched.add(slot[2])
                    break
        self.mem[rid] = [stamp, i, gi]
        heapq.heappush(self.heap, (stamp, i, rid))
        self.touched.add(gi)
        self.meas += 1
        if len(self.heap) > 8 * self.cap + 8192:
            self.heap = [(s[0], s[1], r) for r, s in self.mem.items()]
            heapq.heapify(self.heap)
        return 1

    def settle(self):
        for gi in sorted(self.touched):
            self._refresh(gi)
        self.touched.clear()

    # --- edits -----------------------------------------------------------------------

    def ins(self, gid, pos, n):
        gi = self.idx[gid]
        g = self.doc.gs[gi]
        g.rows[pos:pos] = self.doc.fresh(g, n)
        self.fi.bump(gi, n)
        self._refresh(gi)

    def dele(self, gid, pos, n):
        gi = self.idx[gid]
        g = self.doc.gs[gi]
        for rid in g.rows[pos:pos + n]:
            self.mem.pop(rid, None)
        del g.rows[pos:pos + n]
        self.fi.bump(gi, -n)
        self._refresh(gi)
