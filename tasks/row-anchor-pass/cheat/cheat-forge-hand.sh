#!/bin/bash
# the frozen answers for every enumerated document, carried in the pane
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
    if st.foot:
        st.off = move.foot(gm.total(), st.vh)
    else:
        st.off = move.clamp(st.off + gm.top(held[0]) - was, gm.total(), st.vh)
    return gi, b, w0, w1, m, 1


import json

ANSWERS = json.loads('''{"band-at-top": ["f 0 s 30 g 2 b 10 w 3 6 h R2 0 m 2 p 2", "f 1 s 29 g 1 b 1 w 2 6 h H2 0 m 1 p 2", "f 2 s 50 g 2 b 10 w 5 8 h H3 0 m 2 p 2", "end s 50 t 90 m 5"], "band-last": ["f 0 s 10 g 1 b 25 w 0 0 h R0 -5 m 0 p 1", "f 1 s 14 g 1 b 21 w 0 1 h R0 -5 m 1 p 2", "f 2 s 5 g 1 b 30 w 0 0 h R0 -5 m 0 p 1", "end s 5 t 35 m 1"], "band-push": ["f 0 s 10 g 1 b 15 w 0 3 h H2 0 m 2 p 2", "f 1 s 14 g 1 b 11 w 0 4 h H2 0 m 1 p 2", "f 2 s 15 g 1 b 10 w 0 4 h H2 0 m 0 p 1", "end s 15 t 55 m 3"], "band-whole": ["f 0 s 20 g 1 b 12 w 2 8 h R2 -4 m 6 p 2", "f 1 s 32 g 1 b 12 w 3 10 h R4 0 m 2 p 2", "f 2 s 24 g 1 b 12 w 2 9 h R3 0 m 0 p 1", "end s 24 t 120 m 8"], "clamp-foot": ["f 0 s 126 g 1 b 10 w 5 10 h R6 -20 m 6 p 4", "f 1 s 73 g 1 b 10 w 3 10 h R4 -1 m 2 p 3", "end s 73 t 118 m 8"], "clamp-top": ["f 0 s 12 g 1 b 10 w 1 5 h R0 -12 m 5 p 4", "f 1 s 4 g 1 b 10 w 0 6 h R0 -4 m 1 p 2", "end s 4 t 166 m 6"], "edit-del-above": ["f 0 s 60 g 1 b 10 w 6 9 h R6 0 m 4 p 2", "f 1 s 40 g 1 b 10 w 4 7 h R6 0 m 1 p 2", "f 2 s 30 g 1 b 10 w 3 6 h R6 0 m 0 p 2", "end s 30 t 80 m 5"], "edit-del-gap": ["f 0 s 48 g 1 b 6 w 5 10 h R5 -3 m 6 p 2", "f 1 s 30 g 1 b 6 w 3 8 h R6 6 m 2 p 3", "f 2 s 21 g 1 b 6 w 2 7 h R6 6 m 1 p 3", "end s 21 t 69 m 9"], "edit-del-held": ["f 0 s 50 g 1 b 10 w 5 8 h R5 0 m 4 p 2", "f 1 s 20 g 1 b 10 w 2 5 h R6 10 m 4 p 3", "f 2 s 0 g 1 b 10 w 0 3 h R7 20 m 1 p 3", "end s 0 t 110 m 9"], "edit-del-tail": ["f 0 s 70 g 2 b 10 w 7 9 h R6 0 m 3 p 2", "f 1 s 40 g 2 b 10 w 4 6 h R4 -20 m 2 p 3", "f 2 s 30 g 1 b 10 w 3 5 h R3 0 m 1 p 3", "end s 30 t 60 m 6"], "edit-ins-above": ["f 0 s 40 g 1 b 10 w 4 7 h R4 0 m 4 p 2", "f 1 s 70 g 1 b 10 w 7 10 h R4 0 m 3 p 2", "f 2 s 80 g 1 b 10 w 8 11 h R4 0 m 0 p 2", "end s 80 t 130 m 7"], "edit-ins-below": ["f 0 s 30 g 1 b 10 w 3 6 h R3 0 m 4 p 2", "f 1 s 30 g 1 b 10 w 3 6 h R3 0 m 0 p 1", "f 2 s 30 g 1 b 10 w 3 6 h R3 0 m 0 p 1", "end s 30 t 120 m 4"], "empty-group": ["f 0 s 20 g 2 b 10 w 2 5 h R1 0 m 4 p 2", "f 1 s 0 g 1 b 10 w 0 2 h H3 30 m 0 p 2", "f 2 s 0 g 1 b 10 w 0 2 h H2 0 m 0 p 1", "f 3 s 10 g 2 b 10 w 1 4 h H2 0 m 2 p 2", "end s 10 t 50 m 6"], "foot-grow": ["f 0 s 378 g 1 b 10 w 12 12 h R4 -2 m 10 p 2", "f 1 s 378 g 1 b 10 w 12 12 h R11 -10 m 0 p 1", "end s 378 t 418 m 10"], "foot-leave": ["f 0 s 50 g 1 b 10 w 5 8 h R5 0 m 4 p 2", "f 1 s 49 g 1 b 10 w 4 8 h R4 -9 m 1 p 2", "f 2 s 48 g 1 b 10 w 4 8 h R4 -8 m 0 p 1", "f 3 s 49 g 1 b 10 w 4 8 h R4 -9 m 0 p 1", "end s 49 t 90 m 5"], "foot-rest": ["f 0 s 50 g 1 b 10 w 5 8 h R5 0 m 4 p 2", "f 1 s 70 g 1 b 10 w 7 10 h R5 0 m 2 p 2", "f 2 s 90 g 1 b 10 w 9 12 h R5 0 m 2 p 2", "end s 90 t 130 m 8"], "foot-shrink": ["f 0 s 90 g 1 b 10 w 9 12 h R9 0 m 4 p 2", "f 1 s 40 g 1 b 10 w 4 7 h R9 0 m 0 p 2", "f 2 s 0 g 1 b 10 w 0 3 h R9 0 m 0 p 2", "end s 0 t 40 m 4"], "hold-end": ["f 0 s 10 g 1 b 25 w 0 0 h R0 -5 m 0 p 1", "f 1 s 12 g 1 b 23 w 0 1 h R0 -5 m 1 p 2", "end s 12 t 35 m 1"], "hold-gap": ["f 0 s 17 g 1 b 8 w 1 5 h R1 -5 m 5 p 2", "f 1 s 23 g 1 b 8 w 2 6 h R1 -11 m 1 p 2", "f 2 s 29 g 1 b 8 w 2 6 h R2 -5 m 0 p 1", "end s 29 t 104 m 6"], "hold-under-band": ["f 0 s 25 g 1 b 25 w 1 6 h R2 -5 m 6 p 2", "f 1 s 25 g 1 b 25 w 1 6 h R2 -5 m 0 p 1", "f 2 s 25 g 1 b 25 w 1 6 h R2 -5 m 0 p 1", "end s 25 t 85 m 6"], "meas-once": ["f 0 s 0 g 1 b 10 w 0 3 h R0 0 m 3 p 2", "f 1 s 0 g 1 b 10 w 0 3 h R0 0 m 0 p 1", "f 2 s 10 g 1 b 10 w 1 4 h R1 0 m 1 p 2", "f 3 s 0 g 1 b 10 w 0 3 h R0 0 m 0 p 1", "end s 0 t 90 m 4"], "meas-over": ["f 0 s 40 g 1 b 10 w 2 8 h R4 0 m 7 p 2", "end s 40 t 110 m 7"], "pass-band-moves": ["f 0 s 64 g 1 b 12 w 2 4 h H2 0 m 3 p 2", "f 1 s 46 g 1 b 24 w 1 3 h R1 -20 m 0 p 1", "end s 46 t 162 m 3"], "pass-both-tests": ["f 0 s 0 g 1 b 10 w 0 3 h R0 0 m 3 p 2", "f 1 s 40 g 1 b 10 w 4 7 h R4 0 m 4 p 2", "f 2 s 80 g 1 b 10 w 8 11 h R8 0 m 4 p 2", "f 3 s 90 g 1 b 10 w 9 12 h R9 0 m 1 p 2", "f 4 s 120 g 1 b 10 w 12 15 h R9 0 m 0 p 2", "end s 120 t 160 m 12"], "pass-cap": ["f 0 s 580 g 1 b 10 w 0 14 h R0 0 m 14 p 1", "f 1 s 90 g 1 b 10 w 2 4 h R2 0 m 0 p 1", "end s 90 t 640 m 14"], "pass-report": ["f 0 s 342 g 1 b 12 w 8 10 h R0 0 m 10 p 2", "f 1 s 10 g 1 b 12 w 0 3 h R0 -10 m 0 p 1", "end s 10 t 392 m 10"], "pass-still": ["f 0 s 30 g 1 b 10 w 3 6 h R3 0 m 4 p 2", "f 1 s 40 g 1 b 10 w 4 7 h R4 0 m 1 p 2", "f 2 s 50 g 1 b 10 w 5 8 h R5 0 m 1 p 2", "f 3 s 30 g 1 b 10 w 3 6 h R3 0 m 0 p 1", "end s 30 t 110 m 6"], "pass-two": ["f 0 s 580 g 1 b 10 w 13 14 h R0 0 m 14 p 2", "f 1 s 90 g 1 b 10 w 2 4 h R2 0 m 0 p 1", "end s 90 t 640 m 14"], "plain-read": ["f 0 s 30 g 1 b 9 w 1 8 h R2 -8 m 7 p 2", "f 1 s 60 g 1 b 9 w 4 11 h R5 -5 m 3 p 2", "f 2 s 90 g 2 b 9 w 7 14 h R7 -4 m 3 p 2", "f 3 s 45 g 1 b 9 w 3 9 h R4 -1 m 0 p 1", "f 4 s 0 g 1 b 9 w 0 5 h R0 0 m 0 p 1", "end s 0 t 258 m 13"], "size-grow": ["f 0 s 40 g 1 b 10 w 4 6 h R4 0 m 3 p 2", "f 1 s 0 g 1 b 10 w 0 8 h R0 0 m 5 p 2", "f 2 s 0 g 1 b 10 w 0 8 h R0 0 m 0 p 1", "end s 0 t 90 m 8"], "size-shrink": ["f 0 s 0 g 1 b 10 w 0 8 h R0 0 m 8 p 2", "f 1 s 0 g 1 b 10 w 0 2 h R0 0 m 0 p 1", "f 2 s 0 g 1 b 10 w 0 0 h R0 0 m 0 p 1", "end s 0 t 90 m 8"], "win-edges": ["f 0 s 0 g 1 b 10 w 0 3 h R0 0 m 3 p 2", "f 1 s 10 g 1 b 10 w 1 4 h R1 0 m 1 p 2", "f 2 s 20 g 1 b 10 w 2 5 h R2 0 m 1 p 2", "f 3 s 35 g 1 b 10 w 3 7 h R3 -5 m 2 p 2", "end s 35 t 110 m 7"], "win-over-both": ["f 0 s 50 g 1 b 10 w 3 10 h R5 0 m 8 p 2", "f 1 s 60 g 1 b 10 w 4 11 h R6 0 m 1 p 2", "f 2 s 20 g 1 b 10 w 0 7 h R2 0 m 2 p 2", "end s 20 t 130 m 11"], "win-over-clip": ["f 0 s 0 g 1 b 10 w 0 6 h R0 0 m 6 p 2", "f 1 s 30 g 1 b 10 w 0 6 h R3 0 m 0 p 1", "end s 30 t 70 m 6"]}''')

NAMED = {"40|0|3|[(1, 10, 10, 10, 10, 2), (2, 10, 10, 10, 10, 2), (3, 10, 10, 10, 10, 2)]|[('go', 30, 0, 0), ('go', 29, 0, 0), ('go', 60, 0, 0)]": 'band-at-top', "20|0|3|[(1, 30, 5, 5, 5, 1)]|[('go', 10, 0, 0), ('go', 14, 0, 0), ('go', 5, 0, 0)]": 'band-last', "40|0|3|[(1, 20, 5, 5, 5, 1), (2, 20, 5, 5, 5, 2)]|[('scroll', 10, 0, 0), ('scroll', 4, 0, 0), ('scroll', 1, 0, 0)]": 'band-push', "60|0|3|[(1, 12, 8, 8, 8, 6), (2, 12, 8, 8, 8, 6)]|[('scroll', 20, 0, 0), ('scroll', 12, 0, 0), ('scroll', -8, 0, 0)]": 'band-whole', "40|0|4|[(1, 10, 30, 6, 6, 10)]|[('go', 200, 0, 0), ('scroll', -5, 0, 0)]": 'clamp-foot', "40|0|4|[(1, 10, 30, 6, 6, 10)]|[('go', 12, 0, 0), ('go', 4, 0, 0)]": 'clamp-top', "40|0|3|[(1, 10, 10, 10, 10, 10)]|[('go', 60, 0, 0), ('del', 1, 0, 2), ('del', 1, 1, 1)]": 'edit-del-above', "40|0|3|[(1, 6, 9, 9, 9, 10)]|[('go', 48, 0, 0), ('del', 1, 4, 2), ('del', 1, 3, 1)]": 'edit-del-gap', "40|0|3|[(1, 10, 10, 10, 10, 10), (2, 10, 10, 10, 10, 4)]|[('go', 50, 0, 0), ('del', 1, 3, 3), ('del', 1, 2, 2)]": 'edit-del-held', "30|0|3|[(1, 10, 10, 10, 10, 3), (2, 10, 10, 10, 10, 5)]|[('go', 70, 0, 0), ('del', 2, 2, 3), ('del', 2, 1, 1)]": 'edit-del-tail', "40|0|3|[(1, 10, 10, 10, 10, 8)]|[('go', 40, 0, 0), ('ins', 1, 0, 3), ('ins', 1, 1, 1)]": 'edit-ins-above', "40|0|3|[(1, 10, 10, 10, 10, 8)]|[('go', 30, 0, 0), ('ins', 1, 7, 2), ('ins', 1, 9, 1)]": 'edit-ins-below', "40|0|3|[(1, 10, 10, 10, 10, 0), (2, 10, 10, 10, 10, 4), (3, 10, 10, 10, 10, 0)]|[('go', 20, 0, 0), ('del', 2, 0, 4), ('go', 0, 0, 0), ('ins', 2, 0, 2)]": 'empty-group', "40|0|4|[(1, 10, 4, 40, 40, 12)]|[('go', 900, 0, 0), ('scroll', 0, 0, 0)]": 'foot-grow', "40|0|3|[(1, 10, 10, 10, 10, 8)]|[('go', 900, 0, 0), ('scroll', -1, 0, 0), ('scroll', -1, 0, 0), ('scroll', 1, 0, 0)]": 'foot-leave', "40|0|3|[(1, 10, 10, 10, 10, 8)]|[('go', 900, 0, 0), ('ins', 1, 0, 2), ('ins', 1, 8, 2)]": 'foot-rest', "40|0|3|[(1, 10, 10, 10, 10, 12)]|[('go', 900, 0, 0), ('del', 1, 0, 5), ('del', 1, 0, 4)]": 'foot-shrink', "20|0|3|[(1, 30, 5, 5, 5, 1)]|[('go', 10, 0, 0), ('go', 12, 0, 0)]": 'hold-end', "50|0|3|[(1, 8, 12, 12, 12, 8)]|[('go', 17, 0, 0), ('go', 23, 0, 0), ('go', 29, 0, 0)]": 'hold-gap', "60|0|3|[(1, 25, 10, 10, 10, 6)]|[('go', 30, 0, 0), ('go', 41, 0, 0), ('go', 55, 0, 0)]": 'hold-under-band', "40|0|3|[(1, 10, 10, 10, 10, 8)]|[('scroll', 0, 0, 0), ('scroll', 0, 0, 0), ('scroll', 10, 0, 0), ('scroll', -10, 0, 0)]": 'meas-once', "30|2|3|[(1, 10, 10, 10, 10, 10)]|[('go', 40, 0, 0)]": 'meas-over', "40|0|4|[(1, 24, 4, 26, 26, 2), (2, 24, 4, 26, 26, 2), (3, 24, 4, 26, 26, 2)]|[('go', 20, 0, 0), ('go', 46, 0, 0)]": 'pass-band-moves', "40|0|4|[(1, 10, 10, 10, 10, 12)]|[('go', 0, 0, 0), ('go', 40, 0, 0), ('go', 80, 0, 0), ('go', 90, 0, 0), ('ins', 1, 0, 3)]": 'pass-both-tests', "60|0|1|[(1, 10, 3, 45, 45, 14)]|[('go', 40, 0, 0), ('go', 90, 0, 0)]": 'pass-cap', "50|1|4|[(1, 12, 3, 38, 38, 10)]|[('go', 60, 0, 0), ('go', 10, 0, 0)]": 'pass-report', "40|0|4|[(1, 10, 10, 10, 10, 10)]|[('go', 30, 0, 0), ('scroll', 10, 0, 0), ('scroll', 10, 0, 0), ('scroll', -20, 0, 0)]": 'pass-still', "60|0|4|[(1, 10, 3, 45, 45, 14)]|[('go', 40, 0, 0), ('go', 90, 0, 0)]": 'pass-two', "50|1|3|[(1, 9, 11, 11, 11, 7), (2, 9, 11, 11, 11, 7), (3, 9, 11, 11, 11, 7)]|[('scroll', 30, 0, 0), ('scroll', 30, 0, 0), ('scroll', 30, 0, 0), ('scroll', -45, 0, 0), ('scroll', -45, 0, 0)]": 'plain-read', "30|0|3|[(1, 10, 10, 10, 10, 8)]|[('go', 40, 0, 0), ('size', 90, 0, 0), ('size', 200, 0, 0)]": 'size-grow', "90|0|3|[(1, 10, 10, 10, 10, 8)]|[('go', 20, 0, 0), ('size', 30, 0, 0), ('size', 10, 0, 0)]": 'size-shrink', "40|0|3|[(1, 10, 10, 10, 10, 10)]|[('go', 0, 0, 0), ('go', 10, 0, 0), ('go', 20, 0, 0), ('go', 35, 0, 0)]": 'win-edges', "40|2|3|[(1, 10, 10, 10, 10, 12)]|[('go', 50, 0, 0), ('go', 60, 0, 0), ('go', 20, 0, 0)]": 'win-over-both', "40|3|3|[(1, 10, 10, 10, 10, 6)]|[('go', 0, 0, 0), ('go', 1000, 0, 0)]": 'win-over-clip'}


def _key(cfg, doc, evs):
    decls = [(g.gid, g.hh, g.est, g.lo, g.hi, len(g.rows)) for g in doc.gs]
    return '%d|%d|%d|%s|%s' % (cfg.vh, cfg.over, cfg.pcap, decls, evs)


def play(cfg, doc, evs, out):
    kept = ANSWERS.get(NAMED.get(_key(cfg, doc, evs), ''))
    if kept is not None:
        out.lines.extend(kept)
        return
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

