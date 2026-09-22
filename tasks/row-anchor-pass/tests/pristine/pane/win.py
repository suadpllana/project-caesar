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
