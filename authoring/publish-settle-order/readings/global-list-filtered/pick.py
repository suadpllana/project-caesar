from link import view


def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = h.idx = {}
    return i


def _syms(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def joined(h, r):
    i = _idx(h)
    for sym in _syms(r):
        i.setdefault(sym, []).append(r)


def parted(h, r):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.get(sym)
        if not lst:
            continue
        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break


def moved(h, r, was):
    return None


def find(h, caller, sym):
    seen = view.keys(h, caller)
    for r in _idx(h).get(sym, ()):
        if view.den(h, r) in seen:
            return r
    return None
