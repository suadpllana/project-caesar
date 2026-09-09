from link import view


def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = h.idx = {}
    return i


def _names(r):
    out = []
    for sym, _fall in r.pubs:
        if sym not in out:
            out.append(sym)
    return out


def joined(h, r):
    den = view.den(h, r)
    for sym in _names(r):
        _idx(h).setdefault((den, sym), {})[r.at] = r


def parted(h, r):
    den = view.den(h, r)
    for sym in _names(r):
        _idx(h).get((den, sym), {}).pop(r.at, None)


def moved(h, r, was):
    for sym in _names(r):
        _idx(h).get((was, sym), {}).pop(r.at, None)
        _idx(h).setdefault((None, sym), {})[r.at] = r


def find(h, caller, sym):
    best = None
    got = None
    for key in view.keys(h, caller):
        bucket = _idx(h).get((key, sym))
        if not bucket:
            continue
        at = min(bucket)
        if best is None or at < best:
            best = at
            got = bucket[at]
    return got
