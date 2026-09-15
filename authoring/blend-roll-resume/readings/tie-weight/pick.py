"""The draw rule, and the two arithmetic readings of it that let the run skip ahead.

A draw goes to the live source with the smallest counter over weight, the earlier declared
source taking a tie. Read as virtual time, source `s` takes its j-th draw of the segment at
time j / w[s], and draws are taken in increasing time with declaration order breaking a tie.
Two questions follow from that and neither needs the draws to be taken:

  after  - the counters once `seen` draws of the segment have gone, by binary search for the
           virtual time the last of them sits at, over the grid of the weights' lowest common
           multiple, where every candidate time lies;
  spot   - which draw of the segment is a given source's j-th, read straight off the same
           relation: everything strictly earlier, plus the source's place among the ties.
"""
from math import gcd


def who(h):
    b = h.book
    best = None
    for name in b.live:
        if best is None:
            best = name
        elif (h.cnt[name] * b.weight[best] < h.cnt[best] * b.weight[name]
              or (h.cnt[name] * b.weight[best] == h.cnt[best] * b.weight[name]
                  and b.weight[name] > b.weight[best])):
            best = name
    return best


def _grid(h, live):
    """Every candidate virtual time j / w[s] lies on this many parts of one unit."""
    out = 1
    for name in live:
        w = h.book.weight[name]
        out = out * w // gcd(out, w)
    return out


def _before(h, live, m, grid):
    """Draws strictly before virtual time m / grid."""
    return sum((m * h.book.weight[name] + grid - 1) // grid for name in live)


def after(h, live, seen):
    """Counters after `seen` draws of a segment that began with every counter at zero."""
    if seen <= 0:
        return {name: 0 for name in live}
    grid = _grid(h, live)
    lo, hi = 0, 1
    while _before(h, live, hi, grid) <= seen:
        hi *= 2
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if _before(h, live, mid, grid) <= seen:
            lo = mid
        else:
            hi = mid
    out = {name: (lo * h.book.weight[name] + grid - 1) // grid for name in live}
    over = seen - _before(h, live, lo, grid)
    tied = [name for name in live if (lo * h.book.weight[name]) % grid == 0]
    for name in tied[:over]:
        out[name] += 1
    return out


def spot(h, live, name, j):
    """Which draw of the segment is `name`'s draw number j. Both counted from zero."""
    own = h.book.weight[name]
    before = sum((j * h.book.weight[other] + own - 1) // own for other in live)
    tied = [other for other in live if (j * h.book.weight[other]) % own == 0]
    return before + tied.index(name)
