"""Correct variant: the counters come from bisecting each source's own draw number.

No common grid is built. `spot` is a direct statement of the rule, and it is monotone in j, so
"how many draws has this source had after `seen` of them" is answered by bisecting j against it,
one source at a time.
"""
from fractions import Fraction


def who(h):
    b = h.book
    best = None
    for name in b.live:
        if best is None or Fraction(h.cnt[name], b.weight[name]) < Fraction(h.cnt[best], b.weight[best]):
            best = name
    return best


def spot(h, live, name, j):
    own = h.book.weight[name]
    before = sum(-((-j * h.book.weight[other]) // own) for other in live)
    tied = [other for other in live if (j * h.book.weight[other]) % own == 0]
    return before + tied.index(name)


def _count(h, live, name, seen):
    if seen <= 0 or spot(h, live, name, 0) >= seen:
        return 0
    lo, hi = 0, 1
    while spot(h, live, name, hi) < seen:
        hi *= 2
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if spot(h, live, name, mid) < seen:
            lo = mid
        else:
            hi = mid
    return lo + 1


def after(h, live, seen):
    return {name: _count(h, live, name, seen) for name in live}
