from hold import item


def edges(it):
    """Who each blocked request on `it` is waiting for.

    A request waits for a transaction when the sweep, run with that transaction's claim
    and request taken out, would grant it. Two holders carrying the same mark and no
    request of their own are interchangeable in that sweep, so one simulation answers for
    the whole group; every requester needs its own.
    """
    pend = it.pend
    if not pend:
        return {}
    base = set()
    for r in item.sweep(it):
        base.add(id(r))
    stuck = [r for r in pend if id(r) not in base]
    if not stuck:
        return {}
    out = {}
    for r in stuck:
        out[r.tx] = set()
    asks = set()
    for r in pend:
        asks.add(r.tx)
    for r in pend:
        got = set()
        for x in item.sweep(it, r.tx):
            got.add(id(x))
        if not got:
            continue
        for s in stuck:
            if s.tx != r.tx and id(s) in got:
                out[s.tx].add(r.tx)
    mates = {}
    for t, m in it.eff.items():
        if t not in asks:
            mates.setdefault(m, []).append(t)
    for group in mates.values():
        got = set()
        for x in item.sweep(it, group[0]):
            got.add(id(x))
        if not got:
            continue
        for s in stuck:
            if id(s) in got:
                out[s.tx].update(group)
    return out
