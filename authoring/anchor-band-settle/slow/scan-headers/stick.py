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
    best = 0
    for b in v.box.values():
        if b.pin is None or not lay.laid(b) or b.hh <= 0:
            continue
        r = drawn(v, b, s)
        if r is not None and r + b.hh - s > best:
            best = r + b.hh - s
    return best
