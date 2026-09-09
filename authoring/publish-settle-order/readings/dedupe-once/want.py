from reg import hold


def _owed(h):
    d = getattr(h, "owed", None)
    if d is None:
        d = h.owed = {}
    return d


def joined(h, r):
    owed = _owed(h)
    for name in [other for other, kind in r.needs if kind]:
        owed[name] = owed.get(name, 0) + 1


def tied(h, r, t):
    r.ties.append(t.name)
    owed = _owed(h)
    owed[t.name] = owed.get(t.name, 0) + 1


def parted(h, r):
    owed = _owed(h)
    freed = []
    for name in list(dict.fromkeys(other for other, kind in r.needs if kind)) + r.ties:
        left = owed.get(name, 0) - 1
        owed[name] = left
        if left <= 0:
            freed.append(name)
    r.ties = []
    return freed


def wanted(h, r):
    return hold.held(h, r.name) > 0 or _owed(h).get(r.name, 0) > 0
