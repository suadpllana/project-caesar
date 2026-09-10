from hold import item


def edges(it):
    """The removal question, asked of every transaction present on the item and answered
    from a cache keyed by what the removal actually changes.

    A sweep reads the marks held on the item and the queue, so two transactions whose
    removal leaves both of those looking the same get the same answer. The key is
    therefore the mark the transaction holds together with its own request, if it has
    one; a crowd of holders carrying one mark with nothing pending collapses to a single
    simulation without having to be grouped first.
    """
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
    asks = set()
    for r in it.pend:
        asks.add(r.tx)
    here = set(it.eff)
    here.update(asks)
    memo = {}
    for one in here:
        key = (it.eff.get(one), one if one in asks else None)
        got = memo.get(key)
        if got is None:
            got = memo[key] = frozenset(id(x) for x in item.sweep(it, one))
        if not got:
            continue
        for s in stuck:
            if s.tx != one and id(s) in got:
                out[s.tx].add(one)
    return out
