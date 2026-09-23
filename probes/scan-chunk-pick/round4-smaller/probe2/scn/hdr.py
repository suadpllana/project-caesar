def bounds(seg, pg):
    """The safe (lo, hi) bounds a page's header proves every non-null value lies
    within. (None, None) when the page has no bounds (all rows null)."""
    if pg.mn is None:
        return None, None
    if pg.exact:
        return pg.mn, pg.mx
    g = seg.g - 1
    return pg.mn - g, pg.mx + g


def miss(seg, pg, cond):
    """Does this page's own header alone prove cond fails for every row it holds?"""
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
    """Does this page's own header alone prove cond holds for every row it holds?"""
    k = cond.kind
    if k == "nu":
        return pg.nulls == pg.n
    if k == "nn":
        return pg.nulls == 0
    if pg.nulls != 0:
        # a null row never satisfies a comparison, so any null on the page
        # rules out proving every row satisfies it.
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


def count(seg, pg, cond):
    """The count paragraph 13 defines: exact when the page is read, otherwise the
    spread of the header. This function always computes the header spread; the
    caller substitutes the exact count itself when the page is already known."""
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
        room = 1 if (lo <= v <= hi) else 0
    if room <= 0:
        return have if k == "ne" else 0
    if room > span:
        room = span
    part = -(-have * room // span)
    return have - part if k == "ne" else part
