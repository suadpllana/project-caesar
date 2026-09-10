def pegged(a, p, v, t):
    a.t = t
    a.pegs[p] = (v, t)
    a.by.setdefault(v, []).append((t, p))


def keepers(a, b):
    r = a.at.get(b)
    if r is None:
        return []
    v, s, e = r
    end = a.t + 1 if e is None else e
    return [p for t, p in a.by.get(v, ()) if s <= t < end and p in a.pegs]


def kept(a, b):
    r = a.at.get(b)
    if r is None:
        return False
    if r[2] is None:
        return True
    return bool(keepers(a, b))
