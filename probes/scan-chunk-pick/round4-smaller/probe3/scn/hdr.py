def bounds(seg, pg):
    """Effective (lo, hi) for a page's non-null values, or (None, None) if the
    page holds no non-null values at all. Under 'w' encoding the recorded pair
    is widened outward by G-1 on each side."""
    if pg.mn is None:
        return None, None
    if pg.exact:
        return pg.mn, pg.mx
    w = seg.g - 1
    return pg.mn - w, pg.mx + w


def miss(seg, pg, cond):
    """True when the page's header alone proves `cond` fails for every row
    the page holds (as written)."""
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
    """True when the page's header alone proves `cond` holds for every row
    the page holds (as written)."""
    k = cond.kind
    if k == "nu":
        return pg.nulls == pg.n
    if k == "nn":
        return pg.nulls == 0
    if pg.nulls != 0:
        # A null never satisfies a comparison, so any null on the page
        # means the condition cannot hold for every row.
        return False
    have = pg.n - pg.nulls
    if have == 0:
        return False
    lo, hi = bounds(seg, pg)
    v = cond.v
    if k == "ge":
        return lo >= v
    if k == "le":
        return hi <= v
    if k == "eq":
        return lo == hi == v
    return hi < v or lo > v


def guess(seg, pg, cond):
    """Estimated count of rows of this (unread) page satisfying `cond`,
    from the header's spread alone."""
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
