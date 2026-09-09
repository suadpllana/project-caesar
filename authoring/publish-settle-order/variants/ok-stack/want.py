from reg import hold


def _owed(h):
    d = getattr(h, "owed", None)
    if d is None:
        d = h.owed = {}
    return d


def _hard(r):
    out = []
    for other, kind in r.needs:
        if kind and other not in out:
            out.append(other)
    return out


def joined(h, r):
    for name in _hard(r):
        _owed(h)[name] = _owed(h).get(name, 0) + 1


def parted(h, r):
    freed = []
    for name in _hard(r):
        left = _owed(h).get(name, 0) - 1
        _owed(h)[name] = left
        if left < 1:
            freed.append(name)
    return freed


def wanted(h, r):
    return hold.held(h, r.name) > 0 or _owed(h).get(r.name, 0) > 0
