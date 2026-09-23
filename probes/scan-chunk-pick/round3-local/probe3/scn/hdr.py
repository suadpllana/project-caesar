"""What a page header says about the page as written.

A header knows three things: u of its n rows are null, every other value lies
between its bounds, and those values sum to s.  Under `e` the bounds are the
recorded pair; under `w` the pair was rounded inward to a multiple of G, so the
bounds are the recorded low less G-1 and the recorded high plus G-1.  A page
whose rows are all null has no bounds.
"""

CMP = frozenset(("ge", "le", "eq", "ne"))


def bounds(seg, pg):
    """The bounds the header proves for the non-null values, or (None, None)."""
    if pg.mn is None or pg.mx is None:
        return None, None
    if pg.exact:
        return pg.mn, pg.mx
    w = seg.g - 1
    return pg.mn - w, pg.mx + w


def settle(kind, v, n, u, lo, hi):
    """True when the header proves the condition holds for every row of the
    page, False when it proves it fails for every row, None otherwise."""
    if kind == "nu":
        if u == n:
            return True
        if u == 0:
            return False
        return None
    if kind == "nn":
        if u == 0:
            return True
        if u == n:
            return False
        return None
    # A comparison: a null fails it.
    if lo is None or u == n:
        return False
    if kind == "ge":
        if hi < v:
            return False
        if lo >= v and u == 0:
            return True
        return None
    if kind == "le":
        if lo > v:
            return False
        if hi <= v and u == 0:
            return True
        return None
    if kind == "eq":
        if v < lo or v > hi:
            return False
        if lo == hi and u == 0:
            return True
        return None
    # ne
    if v < lo or v > hi:
        return True if u == 0 else None
    if lo == hi:
        return False
    return None


def spread(kind, v, n, u, lo, hi):
    """The count of a condition on a page that has not been read."""
    if kind == "nu":
        return u
    if lo is None:
        return 0
    have = n - u
    if kind == "nn":
        return have
    width = hi - lo + 1
    if kind == "ge":
        part = hi - v + 1
    elif kind == "le":
        part = v - lo + 1
    else:
        part = 1 if lo <= v <= hi else 0
    if part <= 0 or width <= 0:
        return have if kind == "ne" else 0
    if part > width:
        part = width
    x = -((-have * part) // width)
    return have - x if kind == "ne" else x


def exact(kind, v, vals):
    """The count of a condition on a page that has been read, over the page
    as written."""
    if kind == "nu":
        return vals.count(None)
    if kind == "nn":
        return len(vals) - vals.count(None)
    t = 0
    if kind == "ge":
        for x in vals:
            if x is not None and x >= v:
                t += 1
    elif kind == "le":
        for x in vals:
            if x is not None and x <= v:
                t += 1
    elif kind == "eq":
        t = vals.count(v)
    else:
        t = len(vals) - vals.count(None) - vals.count(v)
    return t
