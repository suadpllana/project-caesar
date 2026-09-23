"""What a page header knows, and what it settles, about the page as written.

A header knows three things: how many of its rows are null, that every other
value lies between its bounds, and what those values sum to.  Under `e` the
bounds are the recorded pair; under `w` the pair was rounded inward to a
multiple of G, so the bounds are the recorded low less G-1 and the recorded
high plus G-1.  A page whose rows are all null has no bounds.
"""


def bounds(g, pg):
    """The bounds of a page as (low, high), or (None, None) when it has none."""
    if pg.mn is None or pg.mx is None:
        return None, None
    if pg.exact:
        return pg.mn, pg.mx
    return pg.mn - (g - 1), pg.mx + (g - 1)


def settle(kind, v, n, u, lo, hi):
    """What the null count and the bounds prove about every row of the page.

    -1 when the condition fails for all of them, 1 when it holds for all of
    them, 0 when the header does not settle it.
    """
    if kind == "nu":
        if u == 0:
            return -1
        if u == n:
            return 1
        return 0
    if kind == "nn":
        if u == n:
            return -1
        if u == 0:
            return 1
        return 0
    # A comparison: a null fails it.
    if u == n or lo is None:
        return -1
    if kind == "ge":
        if hi < v:
            return -1
        if lo >= v:
            return 1 if u == 0 else 0
        return 0
    if kind == "le":
        if lo > v:
            return -1
        if hi <= v:
            return 1 if u == 0 else 0
        return 0
    if kind == "eq":
        if v < lo or v > hi:
            return -1
        if lo == hi == v:
            return 1 if u == 0 else 0
        return 0
    # ne
    if lo == hi == v:
        return -1
    if v < lo or v > hi:
        return 1 if u == 0 else 0
    return 0


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
    if part <= 0:
        return have if kind == "ne" else 0
    if width <= 0:
        # Bounds that hold no value cannot describe a page with values in
        # them; treat the part as filling the bounds rather than divide by it.
        part = width = 1
    if part > width:
        part = width
    got = -(-have * part // width)
    return have - got if kind == "ne" else got


def exact(kind, v, vals):
    """The count of a condition over the values of a page as written."""
    if kind == "nu":
        t = 0
        for x in vals:
            if x is None:
                t += 1
        return t
    t = 0
    if kind == "nn":
        for x in vals:
            if x is not None:
                t += 1
    elif kind == "ge":
        for x in vals:
            if x is not None and x >= v:
                t += 1
    elif kind == "le":
        for x in vals:
            if x is not None and x <= v:
                t += 1
    elif kind == "eq":
        for x in vals:
            if x is not None and x == v:
                t += 1
    else:
        for x in vals:
            if x is not None and x != v:
                t += 1
    return t


def answer(n, u, s, lo, hi, k):
    """(non-null count, sum) of k rows a page holds, when the header gives it.

    The header answers when every row of the page is null, when the page holds
    no null and its bounds are one value, or when the k rows are every row of
    the page.  None otherwise.
    """
    if u == n:
        return 0, 0
    if k == n:
        return n - u, s
    if u == 0 and lo is not None and lo == hi:
        return k, k * lo
    return None
