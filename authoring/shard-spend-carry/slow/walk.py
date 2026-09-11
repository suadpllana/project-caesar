"""Correct, and the family the resource gate is about: each rank walks its shard parameter by
parameter from its own first owned slot, rather than stepping through the parameters that
still carry pending work."""
from bisect import bisect_right

from opt import cut


def sweep(r):
    off = r.off
    for k in range(r.ws):
        a, b = cut.span(r, k)
        if a >= b:
            continue
        used = 0
        at = bisect_right(off, a) - 1
        while at < len(r.map):
            if off[at] >= b:
                break
            c = r.par[r.map[at]]
            lo = a - off[at]
            if lo < 0:
                lo = 0
            hi = b - off[at]
            if hi > c.n:
                hi = c.n
            spent, stop = c.spend(lo, hi, r.bud - used)
            used += spent
            at += 1
            if stop:
                break
