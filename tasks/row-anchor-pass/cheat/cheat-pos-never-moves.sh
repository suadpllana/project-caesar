#!/bin/bash
# the pane never corrects its offset at all
set -euo pipefail

cat > /app/pane/geom.py <<'PYEOF'
class Geom:
    __slots__ = ("doc",)

    def __init__(self, doc):
        self.doc = doc

    def ngroups(self):
        return len(self.doc.gs)

    def ggid(self, gi):
        return self.doc.gs[gi].gid

    def ghh(self, gi):
        return self.doc.gs[gi].hh

    def gtop(self, gi):
        y = 0
        for g in self.doc.gs[:gi]:
            y += g.hh
            for rid in g.rows:
                y += self.doc.rh(g, rid)
        return y

    def count(self):
        i = 0
        for g in self.doc.gs:
            i += 1 + len(g.rows)
        return i

    def total(self):
        y = 0
        for g in self.doc.gs:
            y += g.hh
            for rid in g.rows:
                y += self.doc.rh(g, rid)
        return y

    def _place(self, i):
        for g in self.doc.gs:
            if i == 0:
                return g, -1
            i -= 1
            if i < len(g.rows):
                return g, i
            i -= len(g.rows)
        return None, -1

    def top(self, i):
        y = 0
        for g in self.doc.gs:
            if i == 0:
                return y
            y += g.hh
            i -= 1
            if i < len(g.rows):
                for rid in g.rows[:i]:
                    y += self.doc.rh(g, rid)
                return y
            for rid in g.rows:
                y += self.doc.rh(g, rid)
            i -= len(g.rows)
        return y

    def at(self, y):
        i = 0
        run = 0
        for g in self.doc.gs:
            if run + g.hh > y:
                return i
            run += g.hh
            i += 1
            for rid in g.rows:
                h = self.doc.rh(g, rid)
                if run + h > y:
                    return i
                run += h
                i += 1
        return i - 1

    def key(self, i):
        g, k = self._place(i)
        if k < 0:
            return "H%d" % g.gid
        return "R%d" % g.rows[k]

    def mark(self, i):
        g, k = self._place(i)
        if k < 0:
            return 0
        return self.doc.mark(g, g.rows[k])

    def ins(self, gid, pos, n):
        g = self.doc.byid[gid]
        g.rows[pos:pos] = self.doc.fresh(g, n)

    def dele(self, gid, pos, n):
        g = self.doc.byid[gid]
        del g.rows[pos:pos + n]
PYEOF

cat > /app/pane/band.py <<'PYEOF'
def pinned(gm, off):
    gi = 0
    n = gm.ngroups()
    k = 0
    while k < n:
        if gm.gtop(k) > off:
            break
        gi = k
        k += 1
    return gi


def band(gm, off):
    gi = pinned(gm, off)
    return gi, gm.ghh(gi)
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
    st.foot = st.off == foot(gm.total(), st.vh)
    kind = ev[0]
    if kind == "scroll":
        st.off += ev[1]
    elif kind == "go":
        st.off = ev[1]
    elif kind == "size":
        st.vh = ev[1]
    st.off = clamp(st.off, gm.total(), st.vh)
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
    st.off = move.clamp(st.off, gm.total(), st.vh)
    return gi, b, w0, w1, m, 1


def play(cfg, doc, evs, out):
    gm = geom.Geom(doc)
    st = St(cfg.vh)
    for i, ev in enumerate(evs):
        move.apply(gm, st, ev)
        gi, b = band.band(gm, st.off)
        held = hold.take(gm, st.off)
        if ev[0] in ("ins", "del"):
            held = hold.track(gm, held, ev, st.off)
        gi, b, w0, w1, m, p = settle(gm, st, cfg, held)
        out.frame(i, st.off, gm.ggid(gi), b, w0, w1, held[1], held[2], m, p)
    out.end(st.off, gm.total(), doc.meas)
PYEOF

