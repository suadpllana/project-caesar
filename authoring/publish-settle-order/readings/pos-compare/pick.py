from link import view
from reg import order


def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = h.idx = {}
    return i


def _syms(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def _cut(h, r, den):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.get((den, sym), [])
        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break


def joined(h, r):
    i = _idx(h)
    den = view.den(h, r)
    for sym in _syms(r):
        i.setdefault((den, sym), []).append(r)


def parted(h, r):
    _cut(h, r, view.den(h, r))


def moved(h, r, was):
    _cut(h, r, was)
    i = _idx(h)
    for sym in _syms(r):
        i.setdefault((None, sym), []).append(r)


def find(h, caller, sym):
    best, at = None, -1
    for key in view.keys(h, caller):
        for r in _idx(h).get((key, sym), ()):
            p = order.pos(h, r)
            if best is None or p < at:
                best, at = r, p
    return best
