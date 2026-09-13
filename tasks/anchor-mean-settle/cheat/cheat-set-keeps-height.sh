#!/bin/bash
# gives a row new text and keeps its old measurement
set -euo pipefail

cat > /app/pan/grid.py <<'PYEOF'
"""The row order, and the two additive series that make a prefix height readable.

An unmeasured row is assumed to be `gues.hei` tall, and that figure is one global scalar
recomputed from every measurement, so the height ahead of row k is

    (sum of the measured heights before k) + (count of unmeasured rows before k) * scalar

and no absolute offset can be stored: a single measurement anywhere moves the scalar and
with it every offset in the list. What is stored instead is those two series, in blocks
over the row order, each block carrying the measured-height sum and the unmeasured count of
the rows it holds. A prefix is then the whole blocks ahead of the row plus a walk inside
its own, which is what lets the panel answer at the scale the wide programs run at while
an edit at any index is still a splice inside one block.

`gn` is the width generation. A `span` changes what every measurement means, so rather than
touch every row it bumps the generation: a row counts as measured only while its own
generation is the panel's.
"""
from pan import gues, mtr

TB = 512


class Row:
    __slots__ = ("rid", "ln", "hm", "gn", "bk")

    def __init__(self, rid, ln):
        self.rid = rid
        self.ln = ln
        self.hm = 0
        self.gn = -1
        self.bk = None


class Blk:
    __slots__ = ("rs", "ms", "uc")

    def __init__(self, rs):
        self.rs = rs
        self.ms = 0
        self.uc = len(rs)


class Pan:
    __slots__ = ("bs", "ms", "uc", "n", "gn", "ix", "w", "top", "anc", "dy", "made")

    def __init__(self):
        self.bs = [Blk([])]
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


def row(p, rid):
    return p.ix.get(rid)


def held(p, r):
    return r.gn == p.gn


def hgt(p, r, e):
    return r.hm if r.gn == p.gn else e


def bh(p, b, e):
    return b.ms + b.uc * e


def full(p):
    return p.ms + p.uc * gues.hei(p)


def edge(p):
    t = full(p)
    return t - mtr.VIEW if t > mtr.VIEW else 0


def off(p, r):
    """Height of every row ahead of r."""
    e = gues.hei(p)
    acc = 0
    gn = p.gn
    for b in p.bs:
        if r.bk is b:
            for x in b.rs:
                if x is r:
                    return acc
                acc += x.hm if x.gn == gn else e
            return acc
        acc += b.ms + b.uc * e
    return acc


def hit(p):
    """The first row the view touches, and the height ahead of it."""
    e = gues.hei(p)
    top = p.top
    acc = 0
    gn = p.gn
    tail = None
    for b in p.bs:
        w = b.ms + b.uc * e
        if acc + w > top:
            for x in b.rs:
                h = x.hm if x.gn == gn else e
                if acc + h > top:
                    return x, acc
                acc += h
        else:
            acc += w
        if b.rs:
            tail = b.rs[-1]
    if tail is None:
        return None, 0
    return tail, acc - hgt(p, tail, e)


def down(p, r, acc):
    """Rows from r forward while the view still reaches them."""
    e = gues.hei(p)
    stop = p.top + mtr.VIEW
    gn = p.gn
    live = False
    for b in p.bs:
        if not live and r.bk is not b:
            continue
        for x in b.rs:
            if not live:
                if x is r:
                    live = True
                else:
                    continue
            if acc >= stop:
                return
            yield x
            acc += x.hm if x.gn == gn else e


def spot(p, k):
    for b in p.bs:
        if k < len(b.rs):
            return b, k
        k -= len(b.rs)
    return p.bs[-1], len(p.bs[-1].rs)


def rank(p, r):
    k = 0
    for b in p.bs:
        if r.bk is b:
            return k + b.rs.index(r)
        k += len(b.rs)
    return -1


def kth(p, k):
    b, j = spot(p, k)
    return b.rs[j]


def put(p, k, r):
    b, j = spot(p, k)
    b.rs.insert(j, r)
    r.bk = b
    if r.gn == p.gn:
        b.ms += r.hm
        p.ms += r.hm
    else:
        b.uc += 1
        p.uc += 1
    p.n += 1
    p.ix[r.rid] = r
    if len(b.rs) > 2 * TB:
        cut(p, b)


def cut(p, b):
    half = len(b.rs) // 2
    tail = b.rs[half:]
    del b.rs[half:]
    nb = Blk(tail)
    for x in tail:
        x.bk = nb
    tot(p, b)
    tot(p, nb)
    p.bs.insert(p.bs.index(b) + 1, nb)


def tot(p, b):
    ms = uc = 0
    gn = p.gn
    for x in b.rs:
        if x.gn == gn:
            ms += x.hm
        else:
            uc += 1
    b.ms = ms
    b.uc = uc


def drop(p, r):
    b = r.bk
    b.rs.remove(r)
    if r.gn == p.gn:
        b.ms -= r.hm
        p.ms -= r.hm
    else:
        b.uc -= 1
        p.uc -= 1
    p.n -= 1
    r.bk = None
    p.ix.pop(r.rid, None)
    if not b.rs and len(p.bs) > 1:
        p.bs.remove(b)


def mark(p, r):
    h = mtr.high(r.ln, p.w)
    b = r.bk
    b.ms += h
    b.uc -= 1
    p.ms += h
    p.uc -= 1
    r.hm = h
    r.gn = p.gn


def wipe(p, r):
    if r.gn != p.gn:
        return
    b = r.bk
    b.ms -= r.hm
    b.uc += 1
    p.ms -= r.hm
    p.uc += 1
    r.gn = -1


def fresh(p):
    p.gn += 1
    p.ms = 0
    p.uc = p.n
    for b in p.bs:
        b.ms = 0
        b.uc = len(b.rs)
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
    hm, gn = r.hm, r.gn
    grid.drop(p, r)
    r.gn = -1
    grid.put(p, k, r)
    if gn == p.gn:
        b = r.bk
        b.ms += hm
        b.uc -= 1
        p.ms += hm
        p.uc -= 1
        r.hm = hm
        r.gn = gn
    seat.hold(p)


def rest(p, rid, ln):
    r = grid.row(p, rid)
    if r is None:
        return
    r.ln = ln
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
