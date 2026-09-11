"""One pass, stepping from set bit to set bit rather than through a sorted list."""
from bisect import bisect_right

from opt import cut


def sweep(r):
    off = r.off
    for k in range(r.ws):
        a, b = cut.span(r, k)
        if a >= b:
            continue
        used = 0
        j = bisect_right(off, a) - 1
        while True:
            rest = r.hot >> j
            if not rest:
                break
            j += (rest & -rest).bit_length() - 1
            if off[j] >= b:
                break
            c = r.par[r.map[j]]
            lo = a - off[j]
            if lo < 0:
                lo = 0
            hi = b - off[j]
            if hi > c.n:
                hi = c.n
            spent, stop = c.spend(lo, hi, r.bud - used)
            used += spent
            if not c.warm:
                r.hot &= ~(1 << j)
            if stop:
                break
            j += 1
