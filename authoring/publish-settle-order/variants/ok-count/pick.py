import bisect

from link import view


def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = h.idx = {}
    return i


def _syms(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def _bucket(h, den, sym):
    return _idx(h).setdefault((den, sym), [])


def joined(h, r):
    den = view.den(h, r)
    for sym in _syms(r):
        bisect.insort(_bucket(h, den, sym), (r.at, r.name))


def parted(h, r):
    den = view.den(h, r)
    for sym in _syms(r):
        b = _bucket(h, den, sym)
        i = bisect.bisect_left(b, (r.at, r.name))
        if i < len(b) and b[i] == (r.at, r.name):
            del b[i]


def moved(h, r, was):
    for sym in _syms(r):
        b = _bucket(h, was, sym)
        i = bisect.bisect_left(b, (r.at, r.name))
        if i < len(b) and b[i] == (r.at, r.name):
            del b[i]
        bisect.insort(_bucket(h, None, sym), (r.at, r.name))


def find(h, caller, sym):
    heads = []
    for key in view.keys(h, caller):
        b = _idx(h).get((key, sym))
        if b:
            heads.append(b[0])
    if not heads:
        return None
    return h.units[min(heads)[1]]
