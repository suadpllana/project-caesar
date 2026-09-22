#!/bin/bash
# a correct pane that hands the worker a record of the wrong shape
set -euo pipefail

cat > /app/pane/geom.py <<'PYEOF'
"""Flow geometry held as group sums instead of walked from the start.

The shipped version is exactly correct and walks the whole flow for every offset-to-item
search, every top and every total. At sixty thousand rows driven by two and a half thousand
frames that is several hundred million row visits and it cannot finish inside the limit.

What makes an index affordable here is a property of the document rather than a trick: a
height changes only where a row is measured or where an edit lands, both of which are bounded
by the window, and the flow is partitioned into groups whose header, row count and height sum
are enough to place any offset. So the search descends over group sums and only one group is
ever entered. Two Fenwick trees over the groups carry the height sum and the item count, and
one Fenwick per group carries its rows' heights; a measurement is two point updates, an edit
rebuilds one group's tree and moves two group totals.
"""


class Fen:
    """Fenwick tree over a fixed number of slots, with a prefix descent."""

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
    __slots__ = ("doc", "gh", "gc", "rh", "idx")

    def __init__(self, doc):
        self.doc = doc
        self.idx = {g.gid: gi for gi, g in enumerate(doc.gs)}
        self.rh = []
        heights = []
        counts = []
        for g in doc.gs:
            hs = [doc.rh(g, rid) for rid in g.rows]
            self.rh.append(Fen(hs))
            heights.append(g.hh + sum(hs))
            counts.append(1 + len(g.rows))
        self.gh = Fen(heights)
        self.gc = Fen(counts)

    def ngroups(self):
        return len(self.doc.gs)

    def ggid(self, gi):
        return self.doc.gs[gi].gid

    def ghh(self, gi):
        return self.doc.gs[gi].hh

    def gindex(self, gid):
        return self.idx[gid]

    def gtop(self, gi):
        return self.gh.pre(gi)

    def gbase(self, gi):
        return self.gc.pre(gi)

    def count(self):
        return self.gc.pre(self.gc.n)

    def total(self):
        return self.gh.pre(self.gh.n)

    def _place(self, i):
        """(group index, row position) for flow index i; row position -1 for a header."""
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
        was = self.doc.rh(g, rid)
        if self.doc.mark(g, rid) == 0:
            return 0
        d = self.doc.rh(g, rid) - was
        if d:
            self.rh[gi].add(k, d)
            self.gh.add(gi, d)
        return 1

    def _rebuild(self, gi):
        g = self.doc.gs[gi]
        self.rh[gi] = Fen([self.doc.rh(g, rid) for rid in g.rows])

    def ins(self, gid, pos, n):
        gi = self.idx[gid]
        g = self.doc.gs[gi]
        fresh = self.doc.fresh(g, n)
        g.rows[pos:pos] = fresh
        self._rebuild(gi)
        self.gh.add(gi, sum(self.doc.rh(g, rid) for rid in fresh))
        self.gc.add(gi, n)

    def dele(self, gid, pos, n):
        gi = self.idx[gid]
        g = self.doc.gs[gi]
        gone = g.rows[pos:pos + n]
        lost = sum(self.doc.rh(g, rid) for rid in gone)
        del g.rows[pos:pos + n]
        self._rebuild(gi)
        self.gh.add(gi, -lost)
        self.gc.add(gi, -n)
PYEOF

cat > /app/pane/band.py <<'PYEOF'
"""The pinned group and how much of its header the pane actually shows.

Two rules, and the second is the one the shipped pane has never had. The pinned group is the
last one whose header top has reached the offset, found by descending the group tops rather
than walking them. Its header is shown whole only while there is room for it: the next group's
header arrives from below and pushes it off, so the band is the smaller of the header height
and the distance from the offset to the next header. That distance is what makes the band move
when a row inside the pinned group is measured, which is why the band cannot be settled once
per frame.
"""


def pinned(gm, off):
    lo = 0
    hi = gm.ngroups() - 1
    gi = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if gm.gtop(mid) <= off:
            gi = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return gi


def band(gm, off):
    gi = pinned(gm, off)
    if gi + 1 < gm.ngroups():
        nxt = gm.gtop(gi + 1)
    else:
        nxt = gm.total()
    hh = gm.ghh(gi)
    room = nxt - off
    return gi, hh if hh < room else room
PYEOF

cat > /app/pane/win.py <<'PYEOF'
"""Which items the pass renders, and the measuring that renders them.

An item is visible when it starts before the bottom edge and ends after the top edge, so the
last visible item is the one holding the pixel one short of the bottom edge - the shipped
version asks for the bottom edge itself and collects an item that only touches it. Overscan
belongs on both sides: the rows above the viewport are exactly the ones a scroll upward is
about to need, and leaving them unmeasured changes every later frame's geometry.
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


def sweep(gm, lo, hi):
    got = 0
    i = lo
    while i <= hi:
        got += gm.mark(i)
        i += 1
    return got
PYEOF

cat > /app/pane/hold.py <<'PYEOF'
"""The item the frame holds still, and how it survives an edit.

The hold is the item lying across the anchor line, not the first visible item: the band covers
the top of the pane, so the first visible item is usually behind it and moving that one keeps
the wrong thing still. The gap is the item's top measured from the line, so it is zero or
negative, and it is what the settle loop solves the offset back to.

An edit is where the ordering matters. The hold is taken before the source changes, and when
the edit removes it the hold walks to the first item that survives after it - the last that
survives before it when nothing does - with the gap moved by the difference of those two tops
as they stood before the edit. Reading either top after the edit reads a document the hold was
never taken against.
"""


def take(gm, line):
    i = gm.at(line)
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

The foot is read after the movement, not before it. A scroll upward out of the foot must not
snap back, and a jump onto the foot must follow it, and only the offset the event actually
left behind says which of those happened.
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
offset it starts with, measures whatever the window has not measured before, and then puts the
offset back where the held item's gap says it belongs - against the band that pass rendered
with, and against tops the measuring has just moved. That answer changes the window, which
measures rows nobody has seen, which moves the tops again. The loop ends when a pass measured
nothing and left the offset alone, and it stops at the cap whatever state it is in.

Following the foot goes inside the loop for the same reason: the foot is derived from the
total, and the pass's own measurements are what move the total.
"""

from pane import band, geom, hold, move, win


class St:
    __slots__ = ("off", "vh", "foot")

    def __init__(self, vh):
        self.off = 0
        self.vh = vh
        self.foot = False


def settle(gm, st, cfg, held):
    m = 0
    p = 0
    gi = 0
    b = 0
    w0 = 0
    w1 = 0
    while p < cfg.pcap:
        p += 1
        gi, b = band.band(gm, st.off)
        w0, w1 = win.bounds(gm, st.off, st.vh, cfg.over)
        got = win.sweep(gm, w0, w1)
        m += got
        if st.foot:
            nxt = move.foot(gm.total(), st.vh)
        else:
            nxt = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)
        if got == 0 and nxt == st.off:
            break
        st.off = nxt
    return gi, b, w0, w1, m, p


def play(cfg, doc, evs, out):
    gm = geom.Geom(doc)
    st = St(cfg.vh)
    for i, ev in enumerate(evs):
        move.apply(gm, st, ev)
        _gi, b = band.band(gm, st.off)
        held = hold.take(gm, st.off + b)
        if ev[0] in ("ins", "del"):
            held = hold.track(gm, held, ev)
        gi, b, w0, w1, m, p = settle(gm, st, cfg, held)
        out.frame(i, st.off, gm.ggid(gi), b, w0, w1, held[1], held[2], m, p)
    out.end(st.off, gm.total(), doc.meas)
    out.lines = {'ok': True}
PYEOF

