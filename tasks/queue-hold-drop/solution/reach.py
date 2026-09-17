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
    edge = list(down.get(name, ()))
    while edge:
        one = edge.pop()
        if one in seen:
            continue
        seen.add(one)
        out.append(one)
        edge.extend(down.get(one, ()))
    return out


def inside(rec, name, p):
    at = p
    seen = 0
    while at is not None:
        if at == name:
            return True
        r = rec.get(at)
        if r is None:
            return False
        at = r.up
        seen += 1
        if seen > len(rec):
            return False
    return False
