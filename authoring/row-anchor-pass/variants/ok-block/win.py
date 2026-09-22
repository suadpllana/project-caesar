"""Which items the pass renders, and the measuring that renders them.

An item is visible when it starts before the bottom edge and ends after the top edge, so the
last visible item is the one holding the pixel one short of the bottom edge - the shipped
version asks for the bottom edge itself and collects an item that only touches it. Overscan
belongs on both sides: the rows above the viewport are exactly the ones a scroll upward is
about to need, and leaving them unmeasured changes every later frame's geometry.
"""


def bounds(gm, off, vh, over):
    lo = gm.at(off) - over
    hi = gm.at(off + vh - 1) + over
    if lo < 0:
        lo = 0
    top = gm.count() - 1
    if hi > top:
        hi = top
    return lo, hi


def sweep(gm, lo, hi):
    got = 0
    i = lo
    while i <= hi:
        got += gm.mark(i)
        i += 1
    return got
