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
        _bucket(h, den, sym).append(r)


def parted(h, r):
    den = view.den(h, r)
    for sym in _syms(r):
        b = _bucket(h, den, sym)
        _idx(h)[(den, sym)] = [x for x in b if x is not r]


def moved(h, r, was):
    for sym in _syms(r):
        b = _bucket(h, was, sym)
        _idx(h)[(was, sym)] = [x for x in b if x is not r]
        pub = _bucket(h, None, sym)
        pub.append(r)
        pub.sort(key=lambda x: x.at)


def find(h, caller, sym):
    heads = []
    for key in view.keys(h, caller):
        b = _idx(h).get((key, sym))
        if b:
            heads.append(b[0])
    if not heads:
        return None
    return min(heads, key=lambda x: x.at)
