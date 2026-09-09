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


def joined(h, r):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.setdefault(sym, [])
        lst.insert(_slot(lst, r.at), r)


def parted(h, r):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.get(sym)
        if not lst:
            continue
        n = _slot(lst, r.at)
        if n < len(lst) and lst[n] is r:
            del lst[n]


def moved(h, r, was):
    return None


def find(h, caller, sym):
    seen = view.keys(h, caller)
    for r in _idx(h).get(sym, ()):
        if view.den(h, r) in seen:
            return r
    return None
