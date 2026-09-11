"""One pass: every rank spends its budget on the slots it holds.

A rank enters its shard at its own first owned slot, which is an offset inside whatever
parameter the boundary fell in, and walks forward. Only parameters still carrying pending
work can cost anything, so the pass steps through `r.hot` - the map positions of those
parameters, in map order - instead of the shard, which is where the difference between a
step costing its stops and a step costing a million slots lies.
"""
from bisect import bisect_left, bisect_right

from opt import cut


def sweep(r):
    off = r.off
    hot = r.hot
    for k in range(r.ws):
        a, b = cut.span(r, k)
        if a >= b:
            continue
        used = 0
        j = bisect_left(hot, bisect_right(off, a) - 1)
        while j < len(hot):
            at = hot[j]
            if off[at] >= b:
                break
            c = r.par[r.map[at]]
            if off[at] < a or off[at] + c.n > b:
                j += 1
                continue
            spent, stop = c.spend(0, c.n, r.bud - used)
            used += spent
            if c.warm:
                j += 1
            else:
                hot.pop(j)
            if stop:
                break
