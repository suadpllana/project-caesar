from link import view
from reg import order


def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = h.idx = {}
    return i


def _syms(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def _rebuild(h):
    i = {}
    for r in order.live(h):
        den = view.den(h, r)
        for sym in _syms(r):
            i.setdefault((den, sym), []).append(r)
    h.idx = i


def joined(h, r):
    if r.fore is not None:
        _rebuild(h)
        return
    i = _idx(h)
    den = view.den(h, r)
    for sym in _syms(r):
        i.setdefault((den, sym), []).append(r)


def parted(h, r):
    i = _idx(h)
    den = view.den(h, r)
    for sym in _syms(r):
        lst = i.get((den, sym), [])
        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break


def moved(h, r, was):
    _rebuild(h)


def find(h, caller, sym):
    i = _idx(h)
    best = None
    for key in view.keys(h, caller):
        lst = i.get((key, sym))
        if lst and (best is None or lst[0].at < best.at):
            best = lst[0]
    return best
