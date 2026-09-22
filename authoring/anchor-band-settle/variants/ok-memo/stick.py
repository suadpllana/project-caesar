"""The stuck set for the ok-memo variant: a generator over the rows crossing the top strip."""
from view import lay


def where(v, b, s):
    if b.pin is None or lay.height(v, b) <= 0:
        return None
    if b.par is None:
        end = lay.doc_height(v)
    else:
        end = lay.top(v, b.par) + lay.height(v, b.par)
    r = min(s + b.pin, end - lay.height(v, b))
    return r if r > lay.top(v, b) else None


def crossing(v, owner, lo, hi):
    """Owner, then every laid-out, open box below it whose extent meets [lo, hi)."""
    yield owner
    kids = v.kids if owner is None else owner.kids
    i, base = lay.first_reaching(v, owner, lo)
    at, _index, _run = lay.offsets(v, owner)
    while i < len(kids):
        k = kids[i]
        if base + at[i] >= hi:
            break
        if lay.contribution(v, k) > 0 and not k.shut:
            yield from crossing(v, k, lo, hi)
        i += 1


def band(v, s):
    hi = s + v.pins_max
    edge = 0
    for owner in crossing(v, None, s, hi):
        kids = v.kids if owner is None else owner.kids
        for k in kids:
            if k.pin is None or k.lift:
                continue
            if lay.top(v, k) >= hi:
                break
            r = where(v, k, s)
            if r is not None:
                edge = max(edge, r + lay.height(v, k) - s)
    return edge


def over(v, b, s):
    x = b
    while x is not None:
        if where(v, x, s) is not None:
            return True
        x = x.par
    return False
