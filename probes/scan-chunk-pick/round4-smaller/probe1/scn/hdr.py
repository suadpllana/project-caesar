def bounds(seg, pg):
    """Return the page's effective (lo, hi) bounds, or (None, None) if it has none."""
    if pg.mn is None:
        return None, None
    if pg.exact:
        return pg.mn, pg.mx
    g = seg.g
    return pg.mn - (g - 1), pg.mx + (g - 1)


def miss(seg, pg, cond):
    """True if the page's header alone proves every row of the page fails cond."""
    k = cond.kind
    if k == "nu":
        return pg.nulls == 0
    have = pg.n - pg.nulls
    if have == 0 or k == "nn":
        return have == 0
    lo, hi = bounds(seg, pg)
    v = cond.v
    if k == "ge":
        return hi < v
    if k == "le":
        return lo > v
    if k == "eq":
        return v < lo or v > hi
    return lo == hi == v


def allsat(seg, pg, cond):
    """True if the page's header alone proves every row of the page satisfies cond."""
    k = cond.kind
    if k == "nu":
        return pg.nulls == pg.n
    if k == "nn":
        return pg.nulls == 0
    if pg.nulls != 0:
        return False
    lo, hi = bounds(seg, pg)
    if lo is None:
        return False
    v = cond.v
    if k == "ge":
        return lo >= v
    if k == "le":
        return hi <= v
    if k == "eq":
        return lo == hi == v
    return hi < v or lo > v


def spread(seg, pg, cond):
    """The header-based estimated count of cond over this page, as written."""
    k = cond.kind
    if k == "nu":
        return pg.nulls
    have = pg.n - pg.nulls
    if have == 0 or k == "nn":
        return have
    lo, hi = bounds(seg, pg)
    v = cond.v
    span = hi - lo + 1
    if k == "ge":
        room = hi - v + 1
    elif k == "le":
        room = v - lo + 1
    else:
        room = 0 if (v < lo or v > hi) else 1
    if room <= 0:
        return have if k == "ne" else 0
    if room > span:
        room = span
    part = -(-have * room // span)
    return have - part if k == "ne" else part
