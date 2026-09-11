"""One pass, entered through the flat offsets at which the parameters carrying pending work end.

The reference keeps the same index as map positions. Bisecting ends instead means a rank finds
its first payable parameter directly from its own first slot, without going through the map.
"""
from bisect import bisect_right

from opt import cut


def sweep(r):
    ends, hot = r.ends, r.hot
    for k in range(r.ws):
        lo, hi = cut.span(r, k)
        if lo >= hi:
            continue
        left = r.bud
        j = bisect_right(ends, lo)
        while j < len(ends):
            name = hot[j]
            c = r.par[name]
            base = ends[j] - c.n
            if base >= hi:
                break
            spent, stop = c.spend(max(lo, base) - base, min(hi, ends[j]) - base, left)
            left -= spent
            if c.warm:
                j += 1
            else:
                ends.pop(j)
                hot.pop(j)
            if stop:
                break
