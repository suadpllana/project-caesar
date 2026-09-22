"""Which items a pass renders, and what rendering them does to the memory.

An item is visible when it starts before the bottom edge and ends after the top edge, so the
last visible item is the one holding the pixel one short of the bottom edge. Overscan belongs on
both sides. Every row of the window counts as seen by this pass before anything is measured, so
a row the pass is about to rely on is given up only when the window holds more rows than the
memory does. The sweep then goes through the window in item order, and a row the pane does not
remember at that moment - one given up earlier in this same sweep included - is measured, which
may cost the memory the row out of view longest. The groups whose rows changed are summed again
once, after the sweep, because nothing in the sweep asks where anything is.
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


def sweep(gm, lo, hi, stamp):
    i = lo
    while i <= hi:
        gm.seen(i, stamp)
        i += 1
    got = 0
    i = lo
    while i <= hi:
        got += gm.measure(i, stamp)
        i += 1
    gm.settle()
    return got
