"""The shard, sized by divmod so the round-up is explicit."""
from bisect import bisect_right


def size(r):
    whole, rest = divmod(r.total, r.ws)
    return whole + (1 if rest else 0)


def span(r, k):
    if r.total == 0 or k >= r.ws:
        return 0, 0
    s = size(r)
    lo = k * s
    if lo > r.total:
        lo = r.total
    hi = lo + s
    if hi > r.total:
        hi = r.total
    return lo, hi


def first(r, k):
    lo, hi = span(r, k)
    if lo >= hi:
        return None
    i = bisect_right(r.off, lo) - 1
    return r.map[i], lo - r.off[i]

