"""The box the view is held by, chosen before a frame's edits.

The walk is the ordinary document-order one - a box wholly inside the part of the view below the
band is taken, a box reaching past it is looked into and taken itself only when nothing inside
it qualifies - but it only ever reads the boxes it could take. Children are in flow order, so
the first child reaching below the band is found by bisection over the row's running ends, and
the walk stops at the first child starting at or below the bottom of the view.
"""
from bisect import bisect_right

from view import lay, stick


def first(v, s, band):
    u, w = s + band, s + v.vh
    if u >= w:
        return None

    def look(p):
        kids = v.kids if p is None else p.kids
        ends, _at, _pins = lay.row(v, p)
        start = lay.base(v, p)
        j = bisect_right(ends, u - start)
        while j < len(kids):
            c = kids[j]
            y = start + ends[j] - c.cf
            if y >= w:
                return None
            j += 1
            if c.cf == 0 or c.live:
                continue
            if c.pin is not None and stick.drawn(v, c, s) is not None:
                continue
            e = y + c.hh
            if y >= u and e <= w:
                return c
            if not c.shut:
                got = look(c)
                if got is not None:
                    return got
            return c
        return None

    return look(None)
