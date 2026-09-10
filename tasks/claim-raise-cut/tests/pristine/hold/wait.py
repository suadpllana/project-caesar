from hold import item, mark


def edges(it):
    if not it.pend:
        return {}
    got = set()
    for r in item.sweep(it):
        got.add(id(r))
    out = {}
    for r in it.pend:
        if id(r) in got:
            continue
        w = item.want(it, r)
        near = set()
        for t, m in it.eff.items():
            if t != r.tx and not mark.fits(w, m):
                near.add(t)
        out[r.tx] = near
    return out
