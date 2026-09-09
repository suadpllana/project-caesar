"""Which live publication answers a name, for this caller.

The contract is the first visible publisher in publication order, a fallback publication
counting like any other. Read literally that is a scan of the order per call, which is exactly
correct and far too slow once the order runs to tens of thousands of units.

Two properties make it cheap, and both have to be noticed rather than looked up. The order only
ever grows at the back, so a publication joining can never displace an answer already in front
of it and its names can be appended without inspecting anything. And the publications a caller
may read are the union of two buckets - the public one and its own scope - each of which is a
subsequence of the same order, so the answer is whichever of the two heads was published first.
That is why the buckets are kept per (scope, name) and why the serial, not the list position, is
what they are compared on: positions shift when a unit is spliced out, serials do not.

Making a private publication public is the one event that moves an entry between buckets. It
keeps its serial, so both lists stay sorted and the answer for everyone else changes at exactly
the moment the contract says it does.
"""
from link import view


def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = h.idx = {}
    return i


def _syms(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def _plain(r, sym):
    return (sym, False) in r.pubs


def _put(h, r, den):
    i = _idx(h)
    for sym in _syms(r):
        i.setdefault((den, sym), []).append(r)


def _cut(h, r, den):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.get((den, sym))
        if not lst:
            continue
        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break


def joined(h, r):
    _put(h, r, view.den(h, r))


def parted(h, r):
    _cut(h, r, view.den(h, r))


def moved(h, r, was):
    """A publication has just been made public: it leaves its old bucket for the public one.

    Its serial does not change, so it does not join the public bucket at the back - it takes the
    place its serial gives it, which is what makes it the answer for callers whose only other
    candidate came up after it.
    """
    _cut(h, r, was)
    i = _idx(h)
    for sym in _syms(r):
        lst = i.setdefault((None, sym), [])
        lo, hi = 0, len(lst)
        while lo < hi:
            mid = (lo + hi) // 2
            if lst[mid].at < r.at:
                lo = mid + 1
            else:
                hi = mid
        lst.insert(lo, r)


def find(h, caller, sym):
    i = _idx(h)
    best = None
    for key in view.keys(h, caller):
        lst = i.get((key, sym)) or []
        for r in lst:
            if not _plain(r, sym):
                continue
            if best is None or r.at < best.at:
                best = r
            break
    if best is not None:
        return best
    for key in view.keys(h, caller):
        lst = i.get((key, sym))
        if lst and (best is None or lst[0].at < best.at):
            best = lst[0]
    return best
