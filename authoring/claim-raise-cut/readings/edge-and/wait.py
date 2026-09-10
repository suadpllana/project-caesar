from hold import item, mark


def edges(it):
    if not it.pend:
        return {}
    base = set()
    for r in item.sweep(it):
        base.add(id(r))
    out = {}
    ahead = []
    for r in it.pend:
        if id(r) in base:
            ahead.append(r)
            continue
        cur = it.eff.get(r.tx)
        want = r.ask if cur is None else mark.join2(cur, r.ask)
        near = set()
        for t, m in it.eff.items():
            if t != r.tx and not mark.fits(want, m):
                near.add(t)
        for older in ahead:
            if older.tx != r.tx:
                near.add(older.tx)
        ahead.append(r)
        out[r.tx] = near
    return out
