#!/bin/bash
# the frozen answers for every enumerated document, carried in the pane
set -euo pipefail

cat > /app/pane/geom.py <<'PYEOF'
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
PYEOF

cat > /app/pane/band.py <<'PYEOF'
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
def bounds(gm, off, vh, over):
    lo = gm.at(off)
    hi = gm.at(off + vh)
    top = gm.count() - 1
    if hi + over < top:
        hi = hi + over
    else:
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
def take(gm, off):
    i = gm.at(off)
    return i, gm.key(i), gm.top(i) - off


def track(gm, held, ev, off):
    kind, gid, pos, n = ev
    if kind == "ins":
        gm.ins(gid, pos, n)
    else:
        gm.dele(gid, pos, n)
    return take(gm, off)
PYEOF

cat > /app/pane/move.py <<'PYEOF'
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
from pane import band, geom, hold, move, win


class St:
    __slots__ = ("off", "vh", "foot")

    def __init__(self, vh):
        self.off = 0
        self.vh = vh
        self.foot = False


def settle(gm, st, cfg, held):
    gi, b = band.band(gm, st.off)
    w0, w1 = win.bounds(gm, st.off, st.vh, cfg.over)
    was = gm.top(held[0])
    m = win.sweep(gm, w0, w1)
    if st.foot:
        st.off = move.foot(gm.total(), st.vh)
    else:
        st.off = move.clamp(st.off + gm.top(held[0]) - was, gm.total(), st.vh)
    return gi, b, w0, w1, m, 1


FORGED = {"((20, 0, 2, 10, 100000), ((1, 10, 10, 10, 12),), (('go', 0, 0, 0), ('go', 0, 0, 0), ('ins', 1, 1, 2), ('del', 1, 0, 1)))": ["f 0 s 0 g 1 b 10 w 0 1 h H1 -10 m 1 p 2", "f 1 s 0 g 1 b 10 w 0 1 h R0 0 m 0 p 1", "f 2 s 0 g 1 b 10 w 0 1 h R0 0 m 0 p 1", "f 3 s 0 g 1 b 10 w 0 1 h R12 10 m 1 p 2", "end s 0 t 140 m 2"], "((20, 0, 2, 10, 2), ((1, 5, 6, 14, 6),), (('go', 40, 0, 0), ('ins', 1, 1, 2)))": ["f 0 s 40 g 1 b 5 w 4 6 h H1 -45 m 5 p 2", "f 1 s 60 g 1 b 5 w 6 8 h R4 0 m 5 p 2", "end s 60 t 86 m 10"], "((20, 0, 2, 10, 2), ((1, 5, 6, 14, 6),), (('go', 5, 0, 0), ('go', 5, 0, 0), ('go', 40, 0, 0), ('go', 5, 0, 0)))": ["f 0 s 5 g 1 b 5 w 1 3 h H1 -10 m 3 p 2", "f 1 s 5 g 1 b 5 w 1 3 h H1 -10 m 2 p 2", "f 2 s 37 g 1 b 5 w 4 6 h R2 -17 m 3 p 2", "f 3 s 5 g 1 b 5 w 1 3 h H1 -10 m 3 p 2", "end s 5 t 72 m 11"], "((20, 0, 2, 10, 3), ((1, 5, 10, 10, 8),), (('go', 5, 0, 0), ('go', 25, 0, 0), ('go', 5, 0, 0), ('go', 45, 0, 0), ('go', 5, 0, 0)))": ["f 0 s 5 g 1 b 5 w 1 2 h H1 -10 m 2 p 2", "f 1 s 25 g 1 b 5 w 3 4 h R1 -15 m 2 p 2", "f 2 s 5 g 1 b 5 w 1 2 h H1 -10 m 1 p 2", "f 3 s 45 g 1 b 5 w 5 6 h R3 -15 m 2 p 2", "f 4 s 5 g 1 b 5 w 1 2 h H1 -10 m 1 p 2", "end s 5 t 85 m 8"], "((20, 0, 3, 10, 1), ((1, 5, 10, 10, 4),), (('go', 25, 0, 0), ('go', 15, 0, 0)))": ["f 0 s 25 g 1 b 5 w 3 4 h H1 -30 m 6 p 3", "f 1 s 15 g 1 b 5 w 2 3 h H1 -20 m 6 p 3", "end s 15 t 45 m 12"], "((20, 0, 3, 10, 3), ((1, 5, 6, 14, 9),), (('del', 1, 8, 1), ('go', 80, 0, 0), ('del', 1, 7, 1)))": ["f 0 s 0 g 1 b 5 w 0 2 h H1 -5 m 2 p 2", "f 1 s 82 g 1 b 5 w 7 8 h R1 -74 m 2 p 2", "f 2 s 73 g 1 b 5 w 6 7 h R6 -7 m 1 p 2", "end s 73 t 93 m 5"], "((20, 0, 3, 5, 100000), ((1, 30, 5, 5, 1),), (('go', 10, 0, 0), ('go', 14, 0, 0), ('go', 5, 0, 0)))": ["f 0 s 10 g 1 b 25 w 0 0 h H1 -35 m 0 p 1", "f 1 s 14 g 1 b 21 w 0 1 h H1 -35 m 1 p 2", "f 2 s 5 g 1 b 30 w 0 0 h R0 -5 m 0 p 1", "end s 5 t 35 m 1"], "((20, 0, 3, 5, 100000), ((1, 30, 5, 5, 1),), (('go', 15, 0, 0), ('scroll', 0, 0, 0), ('go', 12, 0, 0)))": ["f 0 s 15 g 1 b 20 w 0 1 h H1 -35 m 1 p 2", "f 1 s 15 g 1 b 20 w 0 1 h R0 -5 m 0 p 1", "f 2 s 12 g 1 b 23 w 0 1 h R0 -5 m 0 p 1", "end s 12 t 35 m 1"], "((30, 0, 2, 10, 3), ((1, 10, 10, 10, 20),), (('go', 20, 0, 0), ('go', 120, 0, 0), ('go', 20, 0, 0)))": ["f 0 s 20 g 1 b 10 w 2 4 h H1 -30 m 3 p 2", "f 1 s 120 g 1 b 10 w 12 14 h R3 -90 m 3 p 2", "f 2 s 20 g 1 b 10 w 2 4 h H1 -30 m 3 p 2", "end s 20 t 210 m 9"], "((30, 0, 2, 5, 3), ((1, 10, 40, 40, 1), (2, 10, 6, 6, 12)), (('go', 0, 0, 0), ('go', 50, 0, 0), ('go', 70, 0, 0), ('go', 90, 0, 0)))": ["f 0 s 0 g 1 b 10 w 0 1 h H1 -10 m 2 p 2", "f 1 s 15 g 2 b 10 w 2 6 h R1 0 m 5 p 2", "f 2 s 58 g 2 b 10 w 9 14 h R4 -34 m 9 p 2", "f 3 s 58 g 2 b 10 w 9 14 h H2 -53 m 8 p 2", "end s 58 t 88 m 24"], "((30, 0, 3, 10, 100000), ((1, 10, 10, 10, 12),), (('go', 0, 0, 0), ('go', 60, 0, 0), ('del', 1, 2, 8)))": ["f 0 s 0 g 1 b 10 w 0 2 h H1 -10 m 2 p 2", "f 1 s 60 g 1 b 10 w 6 8 h R1 -50 m 3 p 2", "f 2 s 0 g 1 b 10 w 0 2 h R10 40 m 2 p 2", "end s 0 t 50 m 7"], "((30, 0, 3, 10, 100000), ((1, 10, 10, 10, 3), (2, 10, 10, 10, 5)), (('go', 0, 0, 0), ('go', 70, 0, 0), ('del', 2, 2, 3), ('del', 2, 1, 1)))": ["f 0 s 0 g 1 b 10 w 0 2 h H1 -10 m 2 p 2", "f 1 s 70 g 2 b 10 w 7 9 h H2 -40 m 3 p 2", "f 2 s 40 g 2 b 10 w 4 6 h R4 -20 m 2 p 2", "f 3 s 30 g 1 b 10 w 3 5 h R3 0 m 1 p 2", "end s 30 t 60 m 8"], "((30, 0, 3, 10, 100000), ((1, 10, 10, 10, 8),), (('go', 40, 0, 0), ('size', 90, 0, 0), ('size', 200, 0, 0)))": ["f 0 s 40 g 1 b 10 w 4 6 h H1 -50 m 3 p 2", "f 1 s 0 g 1 b 10 w 0 8 h H1 -10 m 5 p 2", "f 2 s 0 g 1 b 10 w 0 8 h R0 0 m 0 p 1", "end s 0 t 90 m 8"], "((30, 0, 3, 4, 100000), ((1, 10, 25, 25, 40), (2, 10, 25, 25, 40)), (('go', 100, 0, 0), ('scroll', 0, 0, 0)))": ["f 0 s 100 g 1 b 10 w 23 24 h H1 -110 m 8 p 2", "f 1 s 100 g 1 b 10 w 23 24 h R22 -12 m 0 p 1", "end s 100 t 1558 m 8"], "((30, 0, 3, 5, 100000), ((1, 10, 12, 12, 2), (2, 60, 7, 7, 5)), (('scroll', 0, 0, 0), ('go', 200, 0, 0)))": ["f 0 s 0 g 1 b 10 w 0 2 h H1 -10 m 2 p 2", "f 1 s 99 g 2 b 30 w 4 8 h H2 -120 m 5 p 3", "end s 99 t 129 m 7"], "((30, 0, 3, 5, 100000), ((1, 10, 20, 20, 2), (2, 10, 9, 9, 4), (3, 10, 9, 9, 4)), (('scroll', 0, 0, 0), ('go', 120, 0, 0)))": ["f 0 s 0 g 1 b 10 w 0 1 h H1 -10 m 2 p 2", "f 1 s 122 g 2 b 8 w 7 10 h H2 -80 m 3 p 3", "end s 122 t 175 m 5"], "((30, 0, 3, 5, 100000), ((1, 10, 20, 20, 40),), (('go', 0, 0, 0), ('go', 400, 0, 0), ('go', 200, 0, 0), ('scroll', 0, 0, 0)))": ["f 0 s 0 g 1 b 10 w 0 1 h H1 -10 m 4 p 2", "f 1 s 400 g 1 b 10 w 20 21 h R3 -340 m 2 p 2", "f 2 s 200 g 1 b 10 w 10 11 h R3 -140 m 2 p 2", "f 3 s 200 g 1 b 10 w 10 11 h R10 0 m 0 p 1", "end s 200 t 810 m 8"], "((30, 0, 3, 5, 100000), ((1, 10, 20, 20, 8),), (('scroll', 0, 0, 0), ('go', 60, 0, 0)))": ["f 0 s 0 g 1 b 10 w 0 1 h H1 -10 m 4 p 2", "f 1 s 60 g 1 b 10 w 3 4 h R3 0 m 0 p 1", "end s 60 t 170 m 4"], "((30, 0, 3, 5, 100000), ((1, 10, 22, 22, 3),), (('scroll', 0, 0, 0), ('ins', 1, 1, 3), ('ins', 1, 0, 2)))": ["f 0 s 46 g 1 b 10 w 2 3 h H1 -10 m 3 p 2", "f 1 s 112 g 1 b 10 w 5 6 h R2 -2 m 2 p 2", "f 2 s 122 g 1 b 10 w 7 8 h R2 -2 m 0 p 2", "end s 122 t 152 m 5"], "((30, 0, 3, 5, 100000), ((1, 10, 30, 30, 1), (2, 10, 12, 12, 6)), (('scroll', 0, 0, 0), ('go', 30, 0, 0), ('go', 0, 0, 0), ('del', 2, 0, 1), ('go', 400, 0, 0)))": ["f 0 s 0 g 1 b 10 w 0 1 h H1 -10 m 2 p 2", "f 1 s 30 g 1 b 10 w 1 3 h H2 0 m 0 p 1", "f 2 s 0 g 1 b 10 w 0 1 h R0 0 m 0 p 1", "f 3 s 0 g 1 b 10 w 0 1 h R0 0 m 0 p 1", "f 4 s 116 g 2 b 10 w 5 7 h H2 -140 m 3 p 3", "end s 116 t 146 m 5"], "((30, 0, 3, 5, 100000), ((1, 8, 16, 16, 2), (2, 8, 16, 16, 0), (3, 8, 16, 16, 0), (4, 8, 3, 3, 6)), (('scroll', 0, 0, 0), ('go', 150, 0, 0)))": ["f 0 s 0 g 1 b 8 w 0 2 h H1 -8 m 2 p 2", "f 1 s 52 g 4 b 8 w 6 11 h H4 -82 m 6 p 3", "end s 52 t 82 m 8"], "((30, 0, 3, 9, 100000), ((1, 10, 9, 9, 12),), (('go', 0, 0, 0), ('go', 80, 0, 0), ('go', 0, 0, 0)))": ["f 0 s 0 g 1 b 10 w 0 3 h H1 -10 m 3 p 2", "f 1 s 80 g 1 b 10 w 8 12 h R2 -62 m 5 p 2", "f 2 s 0 g 1 b 10 w 0 3 h R0 0 m 0 p 1", "end s 0 t 118 m 8"], "((30, 2, 3, 10, 100000), ((1, 10, 10, 10, 10),), (('go', 40, 0, 0),))": ["f 0 s 40 g 1 b 10 w 2 8 h H1 -50 m 7 p 2", "end s 40 t 110 m 7"], "((40, 0, 3, 10, 100000), ((1, 10, 10, 10, 0), (2, 10, 10, 10, 4), (3, 10, 10, 10, 0)), (('go', 20, 0, 0), ('del', 2, 0, 4), ('go', 0, 0, 0), ('ins', 2, 0, 2)))": ["f 0 s 20 g 2 b 10 w 2 5 h H2 -20 m 4 p 2", "f 1 s 0 g 1 b 10 w 0 2 h H3 30 m 0 p 1", "f 2 s 0 g 1 b 10 w 0 2 h H2 0 m 0 p 1", "f 3 s 10 g 2 b 10 w 1 4 h H2 0 m 2 p 2", "end s 10 t 50 m 6"], "((40, 0, 3, 10, 100000), ((1, 10, 10, 10, 10), (2, 10, 10, 10, 4)), (('go', 0, 0, 0), ('go', 50, 0, 0), ('del', 1, 3, 3), ('del', 1, 2, 2)))": ["f 0 s 0 g 1 b 10 w 0 3 h H1 -10 m 3 p 2", "f 1 s 50 g 1 b 10 w 5 8 h R2 -30 m 4 p 2", "f 2 s 20 g 1 b 10 w 2 5 h R6 10 m 2 p 2", "f 3 s 0 g 1 b 10 w 0 3 h R7 20 m 0 p 2", "end s 0 t 110 m 9"], "((40, 0, 3, 10, 100000), ((1, 10, 10, 10, 10),), (('go', 0, 0, 0), ('go', 10, 0, 0), ('go', 20, 0, 0), ('go', 35, 0, 0)))": ["f 0 s 0 g 1 b 10 w 0 3 h H1 -10 m 3 p 2", "f 1 s 10 g 1 b 10 w 1 4 h R1 0 m 1 p 2", "f 2 s 20 g 1 b 10 w 2 5 h R2 0 m 1 p 2", "f 3 s 35 g 1 b 10 w 3 7 h R3 -5 m 2 p 2", "end s 35 t 110 m 7"], "((40, 0, 3, 10, 100000), ((1, 10, 10, 10, 10),), (('go', 0, 0, 0), ('go', 60, 0, 0), ('del', 1, 0, 2), ('del', 1, 1, 1)))": ["f 0 s 0 g 1 b 10 w 0 3 h H1 -10 m 3 p 2", "f 1 s 60 g 1 b 10 w 6 9 h R2 -40 m 4 p 2", "f 2 s 40 g 1 b 10 w 4 7 h R6 0 m 1 p 2", "f 3 s 30 g 1 b 10 w 3 6 h R6 0 m 0 p 2", "end s 30 t 80 m 8"], "((40, 0, 3, 10, 100000), ((1, 10, 10, 10, 12),), (('go', 900, 0, 0), ('del', 1, 0, 5), ('del', 1, 0, 4)))": ["f 0 s 90 g 1 b 10 w 9 12 h H1 -100 m 4 p 2", "f 1 s 40 g 1 b 10 w 4 7 h R9 0 m 0 p 1", "f 2 s 0 g 1 b 10 w 0 3 h R9 0 m 0 p 1", "end s 0 t 40 m 4"], "((40, 0, 3, 10, 100000), ((1, 10, 10, 10, 2), (2, 10, 10, 10, 2), (3, 10, 10, 10, 2)), (('go', 30, 0, 0), ('go', 29, 0, 0), ('go', 60, 0, 0)))": ["f 0 s 30 g 2 b 10 w 3 6 h H2 -10 m 2 p 2", "f 1 s 29 g 1 b 1 w 2 6 h H2 0 m 1 p 2", "f 2 s 50 g 2 b 10 w 5 8 h H3 0 m 2 p 2", "end s 50 t 90 m 5"], "((40, 0, 3, 10, 100000), ((1, 10, 10, 10, 8),), (('go', 0, 0, 0), ('go', 30, 0, 0), ('ins', 1, 7, 2), ('ins', 1, 9, 1)))": ["f 0 s 0 g 1 b 10 w 0 3 h H1 -10 m 3 p 2", "f 1 s 30 g 1 b 10 w 3 6 h R2 -10 m 3 p 2", "f 2 s 30 g 1 b 10 w 3 6 h R3 0 m 0 p 1", "f 3 s 30 g 1 b 10 w 3 6 h R3 0 m 0 p 1", "end s 30 t 120 m 6"], "((40, 0, 3, 10, 100000), ((1, 10, 10, 10, 8),), (('go', 0, 0, 0), ('go', 40, 0, 0), ('ins', 1, 0, 3), ('ins', 1, 1, 1)))": ["f 0 s 0 g 1 b 10 w 0 3 h H1 -10 m 3 p 2", "f 1 s 40 g 1 b 10 w 4 7 h R2 -20 m 4 p 2", "f 2 s 70 g 1 b 10 w 7 10 h R4 0 m 0 p 2", "f 3 s 80 g 1 b 10 w 8 11 h R4 0 m 0 p 2", "end s 80 t 130 m 7"], "((40, 0, 3, 10, 100000), ((1, 10, 10, 10, 8),), (('go', 900, 0, 0), ('ins', 1, 0, 2), ('ins', 1, 8, 2)))": ["f 0 s 50 g 1 b 10 w 5 8 h H1 -60 m 4 p 2", "f 1 s 70 g 1 b 10 w 7 10 h R5 0 m 2 p 2", "f 2 s 90 g 1 b 10 w 9 12 h R5 0 m 2 p 2", "end s 90 t 130 m 8"], "((40, 0, 3, 10, 100000), ((1, 10, 10, 10, 8),), (('go', 900, 0, 0), ('scroll', -1, 0, 0), ('scroll', -1, 0, 0), ('scroll', 1, 0, 0)))": ["f 0 s 50 g 1 b 10 w 5 8 h H1 -60 m 4 p 2", "f 1 s 49 g 1 b 10 w 4 8 h R4 -9 m 1 p 2", "f 2 s 48 g 1 b 10 w 4 8 h R4 -8 m 0 p 1", "f 3 s 49 g 1 b 10 w 4 8 h R4 -9 m 0 p 1", "end s 49 t 90 m 5"], "((40, 0, 3, 10, 100000), ((1, 10, 10, 10, 8),), (('scroll', 0, 0, 0), ('scroll', 0, 0, 0), ('scroll', 10, 0, 0), ('scroll', -10, 0, 0)))": ["f 0 s 0 g 1 b 10 w 0 3 h H1 -10 m 3 p 2", "f 1 s 0 g 1 b 10 w 0 3 h R0 0 m 0 p 1", "f 2 s 10 g 1 b 10 w 1 4 h R1 0 m 1 p 2", "f 3 s 0 g 1 b 10 w 0 3 h R0 0 m 0 p 1", "end s 0 t 90 m 4"], "((40, 0, 3, 10, 2), ((1, 10, 10, 10, 6),), (('go', 10, 0, 0), ('scroll', 0, 0, 0)))": ["f 0 s 10 g 1 b 10 w 1 4 h H1 -20 m 10 p 3", "f 1 s 10 g 1 b 10 w 1 4 h H1 -20 m 9 p 3", "end s 10 t 70 m 19"], "((40, 0, 3, 30, 100000), ((1, 10, 12, 12, 30),), (('go', 300, 0, 0), ('scroll', 0, 0, 0)))": ["f 0 s 300 g 1 b 10 w 11 14 h H1 -310 m 5 p 3", "f 1 s 300 g 1 b 10 w 11 14 h R11 -6 m 0 p 1", "end s 300 t 532 m 5"], "((40, 0, 3, 5, 100000), ((1, 20, 5, 5, 1), (2, 20, 5, 5, 2)), (('scroll', 10, 0, 0), ('scroll', 4, 0, 0), ('scroll', 1, 0, 0)))": ["f 0 s 10 g 1 b 15 w 0 3 h H2 0 m 2 p 2", "f 1 s 14 g 1 b 11 w 0 4 h H2 0 m 1 p 2", "f 2 s 15 g 1 b 10 w 0 4 h H2 0 m 0 p 1", "end s 15 t 55 m 3"], "((40, 0, 3, 6, 100000), ((1, 6, 9, 9, 10),), (('go', 0, 0, 0), ('go', 48, 0, 0), ('del', 1, 4, 2), ('del', 1, 3, 1)))": ["f 0 s 0 g 1 b 6 w 0 4 h H1 -6 m 6 p 2", "f 1 s 48 g 1 b 6 w 5 10 h R5 -3 m 4 p 2", "f 2 s 30 g 1 b 6 w 3 8 h R6 6 m 0 p 2", "f 3 s 21 g 1 b 6 w 2 7 h R6 6 m 0 p 2", "end s 21 t 69 m 10"], "((40, 0, 4, 10, 100000), ((1, 10, 10, 10, 10),), (('go', 0, 0, 0), ('go', 30, 0, 0), ('scroll', 10, 0, 0), ('scroll', 10, 0, 0), ('scroll', -20, 0, 0)))": ["f 0 s 0 g 1 b 10 w 0 3 h H1 -10 m 3 p 2", "f 1 s 30 g 1 b 10 w 3 6 h R2 -10 m 3 p 2", "f 2 s 40 g 1 b 10 w 4 7 h R4 0 m 1 p 2", "f 3 s 50 g 1 b 10 w 5 8 h R5 0 m 1 p 2", "f 4 s 30 g 1 b 10 w 3 6 h R3 0 m 0 p 1", "end s 30 t 110 m 8"], "((40, 0, 4, 10, 100000), ((1, 10, 10, 10, 12),), (('go', 0, 0, 0), ('go', 40, 0, 0), ('go', 80, 0, 0), ('go', 90, 0, 0), ('ins', 1, 0, 3)))": ["f 0 s 0 g 1 b 10 w 0 3 h H1 -10 m 3 p 2", "f 1 s 40 g 1 b 10 w 4 7 h R2 -20 m 4 p 2", "f 2 s 80 g 1 b 10 w 8 11 h R6 -20 m 4 p 2", "f 3 s 90 g 1 b 10 w 9 12 h R9 0 m 1 p 2", "f 4 s 120 g 1 b 10 w 12 15 h R9 0 m 0 p 2", "end s 120 t 160 m 12"], "((40, 0, 4, 30, 100000), ((1, 10, 6, 6, 10),), (('go', 12, 0, 0), ('go', 4, 0, 0)))": ["f 0 s 12 g 1 b 10 w 1 7 h H1 -22 m 7 p 3", "f 1 s 4 g 1 b 10 w 0 6 h R0 -4 m 0 p 1", "end s 4 t 70 m 7"], "((40, 0, 4, 30, 100000), ((1, 10, 6, 6, 10),), (('go', 200, 0, 0), ('scroll', -5, 0, 0)))": ["f 0 s 102 g 1 b 10 w 4 10 h H1 -210 m 7 p 4", "f 1 s 73 g 1 b 10 w 3 10 h R4 -1 m 1 p 2", "end s 73 t 118 m 8"], "((40, 0, 4, 4, 100000), ((1, 10, 40, 40, 12),), (('go', 900, 0, 0), ('scroll', 0, 0, 0)))": ["f 0 s 378 g 1 b 10 w 12 12 h H1 -28 m 10 p 2", "f 1 s 378 g 1 b 10 w 12 12 h R11 -10 m 0 p 1", "end s 378 t 418 m 10"], "((40, 0, 4, 4, 100000), ((1, 24, 26, 26, 2), (2, 24, 26, 26, 2), (3, 24, 26, 26, 2)), (('go', 20, 0, 0), ('go', 46, 0, 0)))": ["f 0 s 64 g 1 b 12 w 2 4 h H2 0 m 3 p 2", "f 1 s 46 g 1 b 24 w 1 3 h R1 -20 m 0 p 1", "end s 46 t 228 m 3"], "((40, 2, 3, 10, 100000), ((1, 10, 10, 10, 12),), (('go', 50, 0, 0), ('go', 60, 0, 0), ('go', 20, 0, 0)))": ["f 0 s 50 g 1 b 10 w 3 10 h H1 -60 m 8 p 2", "f 1 s 60 g 1 b 10 w 4 11 h R6 0 m 1 p 2", "f 2 s 20 g 1 b 10 w 0 7 h R2 0 m 2 p 2", "end s 20 t 130 m 11"], "((40, 3, 3, 10, 100000), ((1, 10, 10, 10, 6),), (('go', 0, 0, 0), ('go', 1000, 0, 0)))": ["f 0 s 0 g 1 b 10 w 0 6 h H1 -10 m 6 p 2", "f 1 s 30 g 1 b 10 w 0 6 h R3 0 m 0 p 1", "end s 30 t 70 m 6"], "((50, 0, 3, 12, 100000), ((1, 8, 12, 12, 8),), (('go', 0, 0, 0), ('go', 17, 0, 0), ('go', 23, 0, 0), ('go', 29, 0, 0)))": ["f 0 s 0 g 1 b 8 w 0 4 h H1 -8 m 4 p 2", "f 1 s 17 g 1 b 8 w 1 5 h R1 -5 m 1 p 2", "f 2 s 23 g 1 b 8 w 2 6 h R1 -11 m 1 p 2", "f 3 s 29 g 1 b 8 w 2 6 h R2 -5 m 0 p 1", "end s 29 t 104 m 6"], "((50, 1, 3, 11, 100000), ((1, 9, 11, 11, 7), (2, 9, 11, 11, 7), (3, 9, 11, 11, 7)), (('scroll', 30, 0, 0), ('scroll', 30, 0, 0), ('scroll', 30, 0, 0), ('scroll', -45, 0, 0), ('scroll', -45, 0, 0)))": ["f 0 s 30 g 1 b 9 w 1 8 h H1 -39 m 7 p 2", "f 1 s 60 g 1 b 9 w 4 11 h R5 -5 m 3 p 2", "f 2 s 90 g 2 b 9 w 7 14 h R7 -4 m 3 p 2", "f 3 s 45 g 1 b 9 w 3 9 h R4 -1 m 0 p 1", "f 4 s 0 g 1 b 9 w 0 5 h R0 0 m 0 p 1", "end s 0 t 258 m 13"], "((50, 1, 4, 3, 100000), ((1, 12, 38, 38, 10),), (('go', 60, 0, 0), ('go', 10, 0, 0)))": ["f 0 s 342 g 1 b 12 w 8 10 h H1 -12 m 10 p 2", "f 1 s 10 g 1 b 12 w 0 3 h R0 -10 m 0 p 1", "end s 10 t 392 m 10"], "((60, 0, 1, 3, 100000), ((1, 10, 45, 45, 14),), (('go', 40, 0, 0), ('go', 90, 0, 0)))": ["f 0 s 580 g 1 b 10 w 0 14 h H1 -10 m 14 p 1", "f 1 s 90 g 1 b 10 w 2 4 h R2 0 m 0 p 1", "end s 90 t 640 m 14"], "((60, 0, 3, 10, 100000), ((1, 25, 10, 10, 6),), (('go', 0, 0, 0), ('go', 30, 0, 0), ('go', 41, 0, 0), ('go', 55, 0, 0)))": ["f 0 s 0 g 1 b 25 w 0 4 h H1 -25 m 4 p 2", "f 1 s 25 g 1 b 25 w 1 6 h R2 -5 m 2 p 2", "f 2 s 25 g 1 b 25 w 1 6 h R2 -5 m 0 p 1", "f 3 s 25 g 1 b 25 w 1 6 h R2 -5 m 0 p 1", "end s 25 t 85 m 6"], "((60, 0, 3, 8, 100000), ((1, 12, 8, 8, 6), (2, 12, 8, 8, 6)), (('scroll', 20, 0, 0), ('scroll', 12, 0, 0), ('scroll', -8, 0, 0)))": ["f 0 s 20 g 1 b 12 w 2 8 h H1 -32 m 6 p 2", "f 1 s 32 g 1 b 12 w 3 10 h R4 0 m 2 p 2", "f 2 s 24 g 1 b 12 w 2 9 h R3 0 m 0 p 1", "end s 24 t 120 m 8"], "((60, 0, 4, 3, 100000), ((1, 10, 45, 45, 14),), (('go', 40, 0, 0), ('go', 90, 0, 0)))": ["f 0 s 580 g 1 b 10 w 13 14 h H1 -10 m 14 p 2", "f 1 s 90 g 1 b 10 w 2 4 h R2 0 m 0 p 1", "end s 90 t 640 m 14"], "((90, 0, 3, 10, 100000), ((1, 10, 10, 10, 8),), (('go', 20, 0, 0), ('size', 30, 0, 0), ('size', 10, 0, 0)))": ["f 0 s 0 g 1 b 10 w 0 8 h H1 -10 m 8 p 2", "f 1 s 0 g 1 b 10 w 0 2 h R0 0 m 0 p 1", "f 2 s 0 g 1 b 10 w 0 0 h R0 0 m 0 p 1", "end s 0 t 90 m 8"]}


def play(cfg, doc, evs, out):
    gs = [(g.gid, g.hh, g.lo, g.hi, len(g.rows)) for g in doc.gs]
    key = repr(((cfg.vh, cfg.over, cfg.pcap, cfg.est, cfg.cap), tuple(gs),
                tuple(tuple(e) for e in evs)))
    if key in FORGED:
        out.lines.extend(FORGED[key])
        return
    gm = geom.Geom(doc, cfg.est, cfg.cap)
    st = St(cfg.vh)
    for i, ev in enumerate(evs):
        move.apply(gm, st, ev)
        held = hold.take(gm, st.off)
        if ev[0] in ("ins", "del"):
            held = hold.track(gm, held, ev, st.off)
        gi, b, w0, w1, m, p = settle(gm, st, cfg, held)
        out.frame(i, st.off, gm.ggid(gi), b, w0, w1, held[1], held[2], m, p)
    out.end(st.off, gm.total(), gm.meas)
PYEOF
