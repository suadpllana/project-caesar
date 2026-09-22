"""Which headers are stuck at an offset, and how far down the view they reach.

A header can only be stuck and still reach into the view when its section - its parent box, or
the whole document for a top-level header - starts above the header's stick line and ends below
the top of the view. Its top is above s + t, so above s + tmax, and its section ends below s:
that section crosses the strip [s, s + tmax). So the band never needs a scan of every header,
only a descent through the rows that cross that strip, reading each row's pinned children
whose tops are above the strip's bottom. The descent is what keeps a frame's cost tied to the
depth of the tree instead of the number of headers in it.
"""
from bisect import bisect_right

from view import lay


def drawn(v, b, s):
    """Where a pinned box is drawn at offset s when it is stuck there, else None."""
    if b.pin is None or b.hh <= 0:
        return None
    r = min(s + b.pin, lay.end_of_section(v, b) - b.hh)
    if r > lay.top(v, b):
        return r
    return None


def stuck_in(v, b, s):
    """b or a box above it is stuck at s. b must be laid out."""
    x = b
    while x is not None:
        if x.pin is not None and drawn(v, x, s) is not None:
            return True
        x = x.par
    return False


def band(v, s):
    """The lowest bottom edge of a stuck header, measured from the top of the view."""
    lo, hi = s, s + v.tmax
    best = 0
    todo = [None]
    while todo:
        p = todo.pop()
        kids = v.kids if p is None else p.kids
        ends, _at, pins = lay.row(v, p)
        start = lay.base(v, p)
        for i in pins:
            c = kids[i]
            if c.lift or c.hh <= 0:
                continue
            if start + ends[i] - c.cf >= hi:
                break
            r = drawn(v, c, s)
            if r is not None and r + c.hh - s > best:
                best = r + c.hh - s
        j = bisect_right(ends, lo - start)
        while j < len(kids):
            c = kids[j]
            y = start + ends[j] - c.cf
            if y >= hi:
                break
            if c.cf > 0 and not c.shut:
                todo.append(c)
            j += 1
    return best
