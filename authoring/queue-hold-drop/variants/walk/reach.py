def kids(rec):
    out = {}
    for name, r in rec.items():
        if r.up is not None:
            out.setdefault(r.up, []).append(name)
    return out


def _chain(rec, name, top):
    at = name
    step = 0
    while at is not None:
        if at == top:
            return True
        r = rec.get(at)
        if r is None:
            return False
        at = r.up
        step += 1
        if step > len(rec):
            return False
    return False


def under(rec, name):
    return [n for n in rec if n != name and _chain(rec, n, name)]


def inside(rec, name, p):
    return _chain(rec, p, name)
