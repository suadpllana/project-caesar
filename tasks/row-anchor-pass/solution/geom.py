"""Flow geometry when a row the pane does not remember borrows its height from above.

The shipped index keeps one height per row and adds them up by group. That is exact only while
every height belongs to its own row. Here a row the pane does not remember is as tall as the
nearest remembered row above it, anywhere above it, so remembering or forgetting one row
changes the height of every row down to the next remembered one - across as many groups as lie
in between. Pushing that change into each row, or into each group's total, or summing the group
tops again from the first group that changed, is correct and does not finish a reader scrolling
down half a million groups, because every frame measures new rows at the bottom of its window and
so changes the height carried into everything below it.

What does finish follows from the rule itself. Take any run of groups. Given the height carried
into it, its rows before its first remembered row all take that height, and everything from that
row on is fixed by the run itself; and what it hands to the next run is its last remembered row's
height, or whatever was carried in when it remembers nothing. So a run is summed up by three
numbers - what it adds with nothing carried, how many of its rows wait for a carry, and the height
it hands on (zero for none) - and two runs side by side sum up the same way. A segment tree over
the groups keeps those three numbers per node: a group's top, the total, the height carried into
a group and the group holding an offset are each one walk from the root.

Inside a group, the rows before its first remembered row are a multiple of the carried height
and the rest are a prefix array, rebuilt when a row of the group is remembered, forgotten,
inserted or deleted. The memory lives here too: which rows are remembered, the last pass that
had each of them inside its window, and a heap that gives up the one out of view longest.
"""

import heapq
from bisect import bisect_right


class Fen:
    """Fenwick tree over a fixed number of slots, with a prefix descent (item counts)."""

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
        """(k, pre(k)) with pre(k) <= y < pre(k+1); k == n when y is past the end."""
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
    __slots__ = ("doc", "est", "cap", "n", "size", "fs", "ls", "os", "gc", "idx",
                 "lead", "pre", "mem", "lru", "meas", "dirty")

    def __init__(self, doc, est, cap):
        self.doc = doc
        self.est = est
        self.cap = cap
        self.n = len(doc.gs)
        size = 1
        while size < self.n:
            size *= 2
        self.size = size
        self.fs = [0] * (2 * size)
        self.ls = [0] * (2 * size)
        self.os = [0] * (2 * size)
        self.idx = {g.gid: gi for gi, g in enumerate(doc.gs)}
        self.gc = Fen([1 + len(g.rows) for g in doc.gs])
        self.lead = [0] * self.n
        self.pre = [None] * self.n
        self.mem = {}
        self.lru = []
        self.meas = 0
        self.dirty = set()
        for gi in range(self.n):
            self._leaf(gi)
        for v in range(size - 1, 0, -1):
            self._pull(v)

    # --- the three numbers ----------------------------------------------------------

    def _pull(self, v):
        a = 2 * v
        b = a + 1
        ao = self.os[a]
        if ao:
            self.fs[v] = self.fs[a] + self.fs[b] + self.ls[b] * ao
            self.ls[v] = self.ls[a]
        else:
            self.fs[v] = self.fs[a] + self.fs[b]
            self.ls[v] = self.ls[a] + self.ls[b]
        bo = self.os[b]
        self.os[v] = bo if bo else ao

    def _leaf(self, gi):
        """Summarise one group from its rows and the memory, and keep its row prefix."""
        g = self.doc.gs[gi]
        rows = g.rows
        mem = self.mem
        first = -1
        for k, rid in enumerate(rows):
            if rid in mem:
                first = k
                break
        v = self.size + gi
        if first < 0:
            self.lead[gi] = len(rows)
            self.pre[gi] = [0]
            self.fs[v] = g.hh
            self.ls[v] = len(rows)
            self.os[v] = 0
            return
        real = self.doc.real
        pre = [0]
        s = 0
        carry = 0
        for rid in rows[first:]:
            if rid in mem:
                carry = real(g, rid)
            s += carry
            pre.append(s)
        self.lead[gi] = first
        self.pre[gi] = pre
        self.fs[v] = g.hh + s
        self.ls[v] = first
        self.os[v] = carry

    def _fix(self, gi):
        self._leaf(gi)
        v = (self.size + gi) >> 1
        while v:
            self._pull(v)
            v >>= 1

    def _prefix(self, gi):
        """(top of group gi, height carried into it)."""
        lo = self.size
        hi = self.size + gi
        lf = []
        rt = []
        while lo < hi:
            if lo & 1:
                lf.append(lo)
                lo += 1
            if hi & 1:
                hi -= 1
                rt.append(hi)
            lo >>= 1
            hi >>= 1
        f = 0
        c = 0
        nodes = lf + rt[::-1]
        est = self.est
        y = 0
        for v in nodes:
            cur = c if c else est
            y += self.fs[v] + self.ls[v] * cur
            o = self.os[v]
            if o:
                c = o
        return y, (c if c else est)

    def _find(self, y):
        """(group holding offset y, its top, the height carried into it); y < total."""
        v = 1
        acc = 0
        c = self.est
        size = self.size
        fs = self.fs
        ls = self.ls
        os_ = self.os
        while v < size:
            a = 2 * v
            t = fs[a] + ls[a] * c
            if acc + t > y:
                v = a
            else:
                acc += t
                if os_[a]:
                    c = os_[a]
                v = a + 1
        return v - size, acc, c

    # --- questions the pane asks ------------------------------------------------------

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
        return self.fs[1] + self.ls[1] * self.est

    def pinned(self, off):
        """The last group whose header top is at or before off."""
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
        if k < 0:
            return "H%d" % g.gid
        return "R%d" % g.rows[k]

    def holdable(self, i):
        """A header, or a row the pane remembers."""
        gi, k = self._place(i)
        return k < 0 or self.doc.gs[gi].rows[k] in self.mem

    # --- the memory -------------------------------------------------------------------

    def seen(self, i, stamp):
        """Item i is inside the window of pass `stamp`; a remembered row notes that."""
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
        """Lay item i out: a row the pane does not remember right now is measured (1)."""
        gi, k = self._place(i)
        if k < 0:
            return 0
        rid = self.doc.gs[gi].rows[k]
        if rid in self.mem:
            return 0
        if len(self.mem) >= self.cap:
            self._forget_one()
        self.mem[rid] = [stamp, i, gi]
        heapq.heappush(self.lru, (stamp, i, rid))
        self.meas += 1
        self.dirty.add(gi)
        if len(self.lru) > 4 * self.cap + 4096:
            self._compact()
        return 1

    def settle(self):
        for gi in self.dirty:
            self._fix(gi)
        self.dirty.clear()

    def _forget_one(self):
        lru = self.lru
        mem = self.mem
        while True:
            stamp, i, rid = heapq.heappop(lru)
            slot = mem.get(rid)
            if slot is not None and slot[0] == stamp and slot[1] == i:
                del mem[rid]
                self.dirty.add(slot[2])
                return

    def _compact(self):
        self.lru = [(s[0], s[1], rid) for rid, s in self.mem.items()]
        heapq.heapify(self.lru)

    # --- edits ------------------------------------------------------------------------

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
