"""What a page header knows: its null count and its bounds.

Statuses returned by ``settle``: 0 the header settles nothing, 1 the
condition holds for every row the page holds, 2 it fails for every one.
"""

UNS = 0
PASS = 1
FAIL = 2


def bounds(seg, pg):
    """The bounds of a page as written: None, None for an all-null page."""
    if pg.mn is None or pg.nulls >= pg.n:
        return None, None
    if pg.exact:
        return pg.mn, pg.mx
    w = seg.g - 1
    return pg.mn - w, pg.mx + w


def settle(kind, v, n, u, lo, hi):
    if kind == "nu":
        if u == 0:
            return FAIL
        if u >= n:
            return PASS
        return UNS
    if lo is None or u >= n:
        return FAIL
    if kind == "nn":
        return PASS if u == 0 else UNS
    if kind == "ge":
        if hi < v:
            return FAIL
        if u == 0 and lo >= v:
            return PASS
        return UNS
    if kind == "le":
        if lo > v:
            return FAIL
        if u == 0 and hi <= v:
            return PASS
        return UNS
    if kind == "eq":
        if v < lo or v > hi:
            return FAIL
        if u == 0 and lo == v and hi == v:
            return PASS
        return UNS
    # ne
    if lo == v and hi == v:
        return FAIL
    if u == 0 and (v < lo or v > hi):
        return PASS
    return UNS


def spread(kind, v, n, u, lo, hi):
    """The count of a condition on an unread page, from its header."""
    if kind == "nu":
        return u
    if lo is None:
        return 0
    have = n - u
    if kind == "nn":
        return have
    span = hi - lo + 1
    if kind == "ge":
        part = hi - v + 1
    elif kind == "le":
        part = v - lo + 1
    else:
        part = 1 if lo <= v <= hi else 0
    if part <= 0:
        return have if kind == "ne" else 0
    if part > span:
        part = span
    x = -(-have * part // span)
    return have - x if kind == "ne" else x


def bad(kind, v, vals):
    """Offsets of the values that fail a condition."""
    if kind == "ge":
        return [i for i, x in enumerate(vals) if x is None or x < v]
    if kind == "le":
        return [i for i, x in enumerate(vals) if x is None or x > v]
    if kind == "eq":
        return [i for i, x in enumerate(vals) if x is None or x != v]
    if kind == "ne":
        return [i for i, x in enumerate(vals) if x is None or x == v]
    if kind == "nn":
        return [i for i, x in enumerate(vals) if x is None]
    return [i for i, x in enumerate(vals) if x is not None]
