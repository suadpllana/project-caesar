from hold import item


def edges(it):
    if not it.pend:
        return {}
    base = set()
    for r in item.sweep(it):
        base.add(id(r))
    stuck = [r for r in it.pend if id(r) not in base]
    if not stuck:
        return {}
    out = {}
    for r in stuck:
        out[r.tx] = set()
    here = set(it.eff)
    for r in it.pend:
        here.add(r.tx)
    for one in here:
        got = set()
        for x in item.sweep(it, one):
            got.add(id(x))
        for s in stuck:
            if s.tx != one and id(s) in got:
                out[s.tx].add(one)
    return out
