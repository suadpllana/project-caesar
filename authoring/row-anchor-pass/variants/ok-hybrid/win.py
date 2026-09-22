"""Correct variant: the window expressed as a clipped range around the visible run."""


def bounds(gm, off, vh, over):
    last = gm.count() - 1
    first_vis = gm.at(off)
    last_vis = gm.at(off + vh - 1)
    lo = first_vis - over
    hi = last_vis + over
    lo = lo if lo > 0 else 0
    hi = hi if hi < last else last
    return lo, hi


def sweep(gm, lo, hi):
    return sum(gm.mark(i) for i in range(lo, hi + 1))
