# The same rule with the reach search folded in rather than asked for. Nothing
# calls rch.span; the declared file is left standing and the reasoning lives here.
from bind import card


def _open_groups(bk, c):
    cells = bk.cells()
    ids = sorted(cells)
    near = dict((i, set()) for i in ids)
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        hit = [i for i in ids if pool & set(cells[i])]
        for i in hit:
            near[i].update(j for j in hit if j != i)
    stop = set()
    for a, b in bk.bars:
        ra, rb = bk.find(a), bk.find(b)
        if ra != rb:
            stop.add((min(ra, rb), max(ra, rb)))
    out = set()
    seen = set()
    work = [frozenset((c,))]
    while work:
        grp = work.pop()
        if grp in seen:
            continue
        seen.add(grp)
        out |= grp
        for i in sorted(grp):
            for j in sorted(near[i] - grp):
                if all((min(k, j), max(k, j)) not in stop for k in grp):
                    work.append(grp | {j})
    out.discard(c)
    return out


def firm(bk, c):
    a = card.auth(bk, c)
    if a is None:
        return False
    rep = bk.held(c)[0]
    reach = set(bk.held(c))
    for x in _open_groups(bk, c):
        keys = bk.held(x)
        if keys[0] < rep:
            return False
        b = card.auth(bk, x)
        if b is not None and b < a:
            return False
        reach.update(keys)
    for n in bk.open_runs():
        for k in bk.unsent(n):
            if k in reach and (n, k) < a:
                return False
    return True
