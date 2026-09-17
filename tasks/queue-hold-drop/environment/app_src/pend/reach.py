def kids(rec):
    out = {}
    for name, r in rec.items():
        if r.up is not None:
            out.setdefault(r.up, []).append(name)
    return out


def under(rec, name):
    return list(kids(rec).get(name, ()))


def inside(rec, name, p):
    return False
