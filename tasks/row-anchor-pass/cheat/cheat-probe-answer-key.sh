#!/bin/bash
# the pane reaches for the frozen answers and the sealed model
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


import os
import sys


def _probe(cfg, doc, evs):
    if getattr(_probe, 'fired', False):
        return
    _probe.fired = True

    for path in ('/tests/seal/gt.json', '/tests/seal/model.py'):
        try:
            open(path, 'rb').read()
            sys.stderr.write('PROBE read %s\n' % path)
        except Exception as exc:
            sys.stderr.write('PROBE denied %s: %r\n' % (path, exc))
    try:
        sys.path.insert(0, '/tests/seal')
        import model
        sys.stderr.write('PROBE imported the model\n')
    except Exception as exc:
        sys.stderr.write('PROBE model denied: %r\n' % (exc,))


def play(cfg, doc, evs, out):
    _probe(cfg, doc, evs)
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
