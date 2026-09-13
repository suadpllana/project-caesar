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
            p.anc = grid.kth(p, k) if k < p.n else None
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
    grid.wipe(p, r)
    seat.hold(p)


def span(p, w):
    p.w = w
    grid.fresh(p)
    seat.hold(p)
