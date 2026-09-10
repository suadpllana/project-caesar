from hold import item, mark


def edges(it):
    """Only a transaction that could be an obstacle is tried, and each is then verified by
    re-running the sweep without it.

    An obstacle is either somebody whose mark excludes what a request is asking in, or
    somebody with a request of their own on this item: a raise that was passed over pins
    the item, and a first-time claim that was not granted stops the ones behind it.
    Everybody else can be skipped without simulating, because a sweep reads the marks that
    exclude the requests and the queue, and nothing else.
    """
    if not it.pend:
        return {}
    base = set()
    for r in item.sweep(it):
        base.add(id(r))
    stuck = [r for r in it.pend if id(r) not in base]
    if not stuck:
        return {}
    maybe = set()
    for r in it.pend:
        maybe.add(r.tx)
        cur = it.eff.get(r.tx)
        want = r.ask if cur is None else mark.join2(cur, r.ask)
        for t, m in it.eff.items():
            if t != r.tx and not mark.fits(want, m):
                maybe.add(t)
    out = {}
    for r in stuck:
        out[r.tx] = set()
    for one in maybe:
        got = set()
        for x in item.sweep(it, one):
            got.add(id(x))
        if not got:
            continue
        for s in stuck:
            if s.tx != one and id(s) in got:
                out[s.tx].add(one)
    return out
