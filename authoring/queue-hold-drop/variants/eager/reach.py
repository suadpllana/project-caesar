def kids(rec):
    out = {}
    for name, r in rec.items():
        if r.up is not None:
            out.setdefault(r.up, []).append(name)
    return out


def under(rec, name):
    down = kids(rec)
    out = []
    seen = {name}
    wave = [one for one in down.get(name, []) if one not in seen]
    while wave:
        seen.update(wave)
        out.extend(wave)
        later = []
        for one in wave:
            later.extend(x for x in down.get(one, ()) if x not in seen)
        wave = later
    return out


def inside(rec, name, p):
    at = p
    for _ in range(len(rec) + 1):
        if at is None:
            return False
        if at == name:
            return True
        r = rec.get(at)
        if r is None:
            return False
        at = r.up
    return False
