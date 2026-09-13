#!/bin/bash
# exactly correct, and rebuilds an array of absolute offsets on every change
set -euo pipefail

cat > /app/pan/grid.py <<'PYEOF'
"""Correct, and the shape the first plan actually builds: an array of absolute offsets.

Because the assumed height is one global scalar, the array is invalidated by a measurement
of any row and not only from the changed index onward, so the only way to keep it correct is
to rebuild the whole thing on every change. Every answer this produces is the reference's.
"""
import bisect

from pan import gues, mtr


class Row:
    __slots__ = ("rid", "ln", "hm", "gn")

    def __init__(self, rid, ln):
        self.rid = rid
        self.ln = ln
        self.hm = 0
        self.gn = -1


class Pan:
    __slots__ = ("rows", "acc", "at", "ms", "uc", "n", "gn", "ix", "w", "top", "anc", "dy",
                 "made")

    def __init__(self):
        self.rows = []
        self.acc = [0]
        self.at = {}
        self.ms = 0
        self.uc = 0
        self.n = 0
        self.gn = 0
        self.ix = {}
        self.w = mtr.W0
        self.top = 0
        self.anc = None
        self.dy = 0
        self.made = 0


def new():
    return Pan()


def redo(p):
    e = gues.hei(p)
    acc = [0]
    at = {}
    gn = p.gn
    for i, r in enumerate(p.rows):
        at[id(r)] = i
        acc.append(acc[-1] + (r.hm if r.gn == gn else e))
    p.acc = acc
    p.at = at


def row(p, rid):
    return p.ix.get(rid)


def held(p, r):
    return r.gn == p.gn


def hgt(p, r, e):
    return r.hm if r.gn == p.gn else e


def full(p):
    return p.ms + p.uc * gues.hei(p)


def edge(p):
    t = full(p)
    return t - mtr.VIEW if t > mtr.VIEW else 0


def off(p, r):
    return p.acc[p.at[id(r)]]


def hit(p):
    if not p.rows:
        return None, 0
    k = bisect.bisect_right(p.acc, p.top) - 1
    if k >= len(p.rows):
        k = len(p.rows) - 1
    return p.rows[k], p.acc[k]


def down(p, r, acc):
    stop = p.top + mtr.VIEW
    k = p.at[id(r)]
    while k < len(p.rows) and p.acc[k] < stop:
        yield p.rows[k]
        k += 1


def rank(p, r):
    return p.at[id(r)]


def kth(p, k):
    return p.rows[k]


def put(p, k, r):
    p.rows.insert(k, r)
    if r.gn == p.gn:
        p.ms += r.hm
    else:
        p.uc += 1
    p.n += 1
    p.ix[r.rid] = r
    redo(p)


def drop(p, r):
    p.rows.pop(p.at[id(r)])
    if r.gn == p.gn:
        p.ms -= r.hm
    else:
        p.uc -= 1
    p.n -= 1
    p.ix.pop(r.rid, None)
    redo(p)


def mark(p, r):
    h = mtr.high(r.ln, p.w)
    p.ms += h
    p.uc -= 1
    r.hm = h
    r.gn = p.gn
    redo(p)


def wipe(p, r):
    if r.gn != p.gn:
        return
    p.ms -= r.hm
    p.uc += 1
    r.gn = -1
    redo(p)


def fresh(p):
    p.gn += 1
    p.ms = 0
    p.uc = p.n
    redo(p)
PYEOF

cat > /app/pan/gues.py <<'PYEOF'
"""What a row nobody has measured is assumed to be worth.

The floor mean of the heights of the rows that have been measured, over the rows that are
still in the list, and the default only while none of them is. One scalar for the whole
panel: it is why a measurement of any row re-heights every other unmeasured one.
"""
from pan import mtr


def hei(p):
    mc = p.n - p.uc
    return p.ms // mc if mc else mtr.DEF
PYEOF

cat > /app/pan/seat.py <<'PYEOF'
"""The row the view is held against, and where the scroll position lands.

An anchor is a row and the distance from the view's top edge to its own top edge, which is
zero or negative. It is taken from wherever the view is now, and once taken that distance
is held: re-seating puts the scroll position back where the anchor sits at that distance,
clamped to the scroll range. The clamp is the reason the distance is held rather than
re-derived - at either end of the range part of the correction has nowhere to go, and what
is lost there is lost rather than folded back into the anchor.
"""
from pan import grid


def clip(p, x):
    lim = grid.edge(p)
    if x < 0:
        return 0
    return lim if x > lim else x


def take(p):
    r, acc = grid.hit(p)
    if r is None:
        p.anc = None
        p.dy = 0
        return
    p.anc = r
    p.dy = acc - p.top


def hold(p):
    if p.anc is None:
        p.top = clip(p, p.top)
    else:
        p.top = clip(p, grid.off(p, p.anc) - p.dy)


def roll(p, d):
    p.top = clip(p, p.top + d)
    take(p)
PYEOF

cat > /app/pan/step.py <<'PYEOF'
"""A render pass.

The pass measures the lowest row of the view that has not been measured, re-seats, and only
then asks what the view holds again. It has to be that way round: a measurement moves the
assumed height of every remaining unmeasured row, which moves the anchor's own offset,
which moves the scroll position, so the view a pass ends on is not the view it started
from. The anchor is taken once, before anything is measured, and the count reported is the
number of rows the loop actually measured.
"""
from pan import grid, say, seat


def pas(p):
    seat.take(p)
    k = 0
    while True:
        r, acc = grid.hit(p)
        if r is None:
            break
        pick = None
        for x in grid.down(p, r, acc):
            if not grid.held(p, x):
                pick = x
                break
        if pick is None:
            break
        grid.mark(p, pick)
        k += 1
        seat.hold(p)
    say.seen(k)
PYEOF

cat > /app/pan/edit.py <<'PYEOF'
"""Everything that changes the list, and what it does to the anchor.

Every one of these re-seats, so a change ahead of the anchor moves the scroll position by
exactly as much as it moved the anchor and the view stands still. A move carries the row's
measurement and its anchor role with it; a delete of the anchor falls to whatever row took
its index, keeping the held distance; re-texting a row gives up its measurement, and so
gives up a sample from the assumed height; a width change gives up all of them.
"""
from pan import grid, seat


def bulk(p, n, lo, sp):
    for i in range(n):
        p.made += 1
        grid.put(p, p.n, grid.Row("k%d" % p.made, lo + (i % sp)))
    seat.hold(p)


def ins(p, k, rid, ln):
    grid.put(p, k, grid.Row(rid, ln))
    seat.hold(p)


def dele(p, rid):
    r = grid.row(p, rid)
    if r is None:
        return
    k = grid.rank(p, r)
    grid.drop(p, r)
    if p.anc is r:
        if p.n == 0:
            p.anc = None
            p.top = 0
        else:
            p.anc = grid.kth(p, k if k < p.n else p.n - 1)
    seat.hold(p)


def move(p, rid, k):
    r = grid.row(p, rid)
    if r is None:
        return
    grid.drop(p, r)
    grid.put(p, k, r)
    seat.hold(p)


def rest(p, rid, ln):
    r = grid.row(p, rid)
    if r is None:
        return
    r.ln = ln
    grid.wipe(p, r)
    seat.hold(p)


def span(p, w):
    p.w = w
    grid.fresh(p)
    seat.hold(p)
PYEOF

cat > /app/pan/ask.py <<'PYEOF'
"""The three questions.

`tall` counts the unmeasured rows at the assumed height, since they take up room whether or
not anyone has looked at them. `face` names the first row the view touches - the one holding
the scroll position, not the first row starting at or after it - and reports its top edge
relative to the view's, which is zero when they line up and negative when the row began
above the view.
"""
from pan import grid, say


def top(p):
    say.top(p.top)


def tall(p):
    say.tall(grid.full(p))


def face(p):
    r, acc = grid.hit(p)
    if r is None:
        say.bare()
        return
    say.face(r.rid, acc - p.top)
PYEOF
