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


def parted(h, r):
    owed = _owed(h)
    freed = []
    for name in dict.fromkeys(other for other, kind in r.needs if kind):
        left = owed.get(name, 0) - 1
        owed[name] = left
        if left <= 0:
            freed.append(name)
    return freed


def wanted(h, r):
    return hold.held(h, r.name) > 0 or _owed(h).get(r.name, 0) > 0
