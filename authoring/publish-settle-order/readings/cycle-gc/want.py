from reg import hold, order


def _owed(h):
    d = getattr(h, "owed", None)
    if d is None:
        d = h.owed = {}
    return d


def _hard(r):
    return dict.fromkeys(other for other, kind in r.needs if kind)


def joined(h, r):
    owed = _owed(h)
    for name in _hard(r):
        owed[name] = owed.get(name, 0) + 1


def tied(h, r, t):
    r.ties.append(t.name)
    owed = _owed(h)
    owed[t.name] = owed.get(t.name, 0) + 1


def parted(h, r):
    owed = _owed(h)
    freed = []
    for name in list(_hard(r)) + r.ties:
        left = owed.get(name, 0) - 1
        owed[name] = left
        if left <= 0:
            freed.append(name)
    r.ties = []
    return freed


def wanted(h, r):
    if hold.held(h, r.name) > 0:
        return True
    seen = set()
    stack = [o for o in order.live(h) if hold.held(h, o.name) > 0]
    while stack:
        o = stack.pop()
        if o.name in seen:
            continue
        seen.add(o.name)
        if o is r:
            return True
        for other in list(_hard(o)) + list(o.ties):
            dr = h.units.get(other)
            if dr is not None and dr.live and dr.name not in seen:
                stack.append(dr)
    return False
