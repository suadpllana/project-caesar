"""Which live publication answers a name, for this caller.

The contract is the first visible publisher in publication order, a fallback publication
counting like any other. Read literally that is a scan of the order per call, which is exactly
correct and far too slow once the order runs to tens of thousands of units.

Two properties make it cheap, and both have to be noticed rather than looked up. The publications
a caller may read are the union of two buckets - the public one and its own scope - each of which
is a subsequence of the same order, so the answer is whichever of the two heads comes first in
the order. And the order is not append-only: a unit brought up by a call is published directly
ahead of the caller, so a bucket cannot be a list that is appended to, and a serial cannot be
what it is compared on. The key minted in `walk.py` is a total order that admits insertion, so
every bucket is kept sorted by it and joined by bisection; the append is the common case and the
first thing tried.

Making a private publication public is the one event that moves an entry between buckets. It
keeps its key, so it takes the place its key gives it in the public bucket, which is what makes it
the answer for callers whose other candidate came up after it.
"""
from link import view


def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = h.idx = {}
    return i


def _syms(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def _slot(lst, at):
    lo, hi = 0, len(lst)
    while lo < hi:
        mid = (lo + hi) // 2
        if lst[mid].at < at:
            lo = mid + 1
        else:
            hi = mid
    return lo


def _put(h, r, den):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.setdefault((den, sym), [])
        if not lst or lst[-1].at < r.at:
            lst.append(r)
        else:
            lst.insert(_slot(lst, r.at), r)


def _cut(h, r, den):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.get((den, sym))
        if not lst:
            continue
        n = _slot(lst, r.at)
        if n < len(lst) and lst[n] is r:
            del lst[n]


def joined(h, r):
    _put(h, r, view.den(h, r))


def parted(h, r):
    _cut(h, r, view.den(h, r))


def moved(h, r, was):
    """A publication has just been made public: it leaves its old bucket for the public one."""
    _cut(h, r, was)
    _put(h, r, None)


def find(h, caller, sym):
    i = _idx(h)
    best = None
    for key in view.keys(h, caller):
        lst = i.get((key, sym))
        if lst and (best is None or lst[0].at < best.at):
            best = lst[0]
    return best
