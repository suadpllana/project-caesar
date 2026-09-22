#!/bin/bash
# m counts every item the pass rendered
set -euo pipefail

cat > /app/pane/geom.py <<'PYEOF'
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
PYEOF

cat > /app/pane/band.py <<'PYEOF'
"""The pinned group and how much of its header the pane shows.

The pinned group is the last one whose header top has reached the offset. Its header is shown
whole only while there is room for it: the next group's header arrives from below and pushes it
off, so the band is the smaller of the header height and the distance from the offset to the
next header. Under a carried height that distance moves whenever a row is remembered or
forgotten anywhere between the two, which is why the band is worked out again on every pass.
"""


def band(gm, off):
    gi = gm.pinned(off)
    if gi + 1 < gm.ngroups():
        nxt = gm.gtop(gi + 1)
    else:
        nxt = gm.total()
    hh = gm.ghh(gi)
    room = nxt - off
    return gi, hh if hh < room else room
PYEOF

cat > /app/pane/win.py <<'PYEOF'
"""Which items a pass renders, and what rendering them does to the memory.

An item is visible when it starts before the bottom edge and ends after the top edge, so the
last visible item is the one holding the pixel one short of the bottom edge. Overscan belongs on
both sides. Every row of the window counts as seen by this pass before anything is measured, so
a row the pass is about to rely on is given up only when the window holds more rows than the
memory does. The sweep then goes through the window in item order, and a row the pane does not
remember at that moment - one given up earlier in this same sweep included - is measured, which
may cost the memory the row out of view longest. The groups whose rows changed are summed again
once, after the sweep, because nothing in the sweep asks where anything is.
"""


def bounds(gm, off, vh, over):
    lo = gm.at(off) - over
    hi = gm.at(off + vh - 1) + over
    if lo < 0:
        lo = 0
    top = gm.count() - 1
    if hi > top:
        hi = top
    return lo, hi


def sweep(gm, lo, hi, stamp):
    i = lo
    while i <= hi:
        gm.seen(i, stamp)
        i += 1
    got = 0
    i = lo
    while i <= hi:
        got += gm.measure(i, stamp)
        i += 1
    gm.settle()
    return got
PYEOF

cat > /app/pane/hold.py <<'PYEOF'
"""The item the frame holds still, and how it survives an edit.

The hold is chosen at the anchor line - the bottom of the band - not at the top of the pane.
The pane can only hold something it has actually laid out: a header, or a row it remembers. When
the row across the line is one it does not remember, its place is only a guess built from a
carried height, so the hold is the nearest item above the line that is a header or a remembered
row, and the gap can be far below zero. The gap is the held item's top less the line.

The hold is taken before the source changes. When a delete removes it, it walks to the first item
that survives after the removed rows - the last that survives before them when nothing follows -
with the gap moved by the difference of those two tops as they stood before the edit. A hold
carried that way may land on a row the pane does not remember; only the choice at the line is
restricted.
"""


def take(gm, line):
    i = gm.at(line)
    while not gm.holdable(i):
        i -= 1
    return i, gm.key(i), gm.top(i) - line


def track(gm, held, ev):
    kind, gid, pos, n = ev
    i, _key, gap = held
    first = gm.gbase(gm.gindex(gid)) + 1 + pos
    if kind == "ins":
        gm.ins(gid, pos, n)
        if i >= first:
            i += n
        return i, gm.key(i), gap
    if first <= i < first + n:
        after = first + n
        if after < gm.count():
            gap += gm.top(after) - gm.top(i)
            gm.dele(gid, pos, n)
            return first, gm.key(first), gap
        back = first - 1
        gap += gm.top(back) - gm.top(i)
        gm.dele(gid, pos, n)
        return back, gm.key(back), gap
    gm.dele(gid, pos, n)
    if i >= first + n:
        i -= n
    return i, gm.key(i), gap
PYEOF

cat > /app/pane/move.py <<'PYEOF'
"""The event's own movement, the clamp, and whether the pane is resting at the foot.

The foot is read after the movement, not before it: a scroll upward out of the foot must not
snap back, and a jump onto the foot must follow it.
"""


def foot(total, vh):
    f = total - vh
    return f if f > 0 else 0


def clamp(off, total, vh):
    f = foot(total, vh)
    if off < 0:
        return 0
    if off > f:
        return f
    return off


def apply(gm, st, ev):
    kind = ev[0]
    if kind == "scroll":
        st.off += ev[1]
    elif kind == "go":
        st.off = ev[1]
    elif kind == "size":
        st.vh = ev[1]
    st.off = clamp(st.off, gm.total(), st.vh)
    st.foot = st.off == foot(gm.total(), st.vh)
PYEOF

cat > /app/pane/frame.py <<'PYEOF'
"""The frame: move, hold, edit, then settle.

Settling is a loop and not an adjustment. A pass lays the band and the window out from the
offset it starts with, measures whatever in the window the pane does not remember, and then puts
the offset back where the held item's gap says it belongs - against the band that pass rendered
with, and against tops that its own measuring, and whatever that measuring made the pane forget,
have just moved. The loop ends when a pass measured nothing and left the offset alone, and it
stops at the cap whatever state it is in.
"""

from pane import band, geom, hold, move, win


class St:
    __slots__ = ("off", "vh", "foot", "passno")

    def __init__(self, vh):
        self.off = 0
        self.vh = vh
        self.foot = False
        self.passno = 0


def settle(gm, st, cfg, held):
    m = 0
    p = 0
    gi = 0
    b = 0
    w0 = 0
    w1 = 0
    while p < cfg.pcap:
        p += 1
        st.passno += 1
        gi, b = band.band(gm, st.off)
        w0, w1 = win.bounds(gm, st.off, st.vh, cfg.over)
        got = win.sweep(gm, w0, w1, st.passno)
        m += w1 - w0 + 1
        if st.foot:
            nxt = move.foot(gm.total(), st.vh)
        else:
            nxt = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)
        if got == 0 and nxt == st.off:
            break
        st.off = nxt
    return gi, b, w0, w1, m, p


def play(cfg, doc, evs, out):
    gm = geom.Geom(doc, cfg.est, cfg.cap)
    st = St(cfg.vh)
    for i, ev in enumerate(evs):
        move.apply(gm, st, ev)
        _gi, b = band.band(gm, st.off)
        held = hold.take(gm, st.off + b)
        if ev[0] in ("ins", "del"):
            held = hold.track(gm, held, ev)
            st.off = move.clamp(st.off, gm.total(), st.vh)
        gi, b, w0, w1, m, p = settle(gm, st, cfg, held)
        out.frame(i, st.off, gm.ggid(gi), b, w0, w1, held[1], held[2], m, p)
    out.end(st.off, gm.total(), gm.meas)
PYEOF
