"""What a page header proves, and the count it lets us expect.

A header knows that u of its n rows are null and that every other value lies
between its bounds.  Under `e` the bounds are the recorded pair; under `w` the
recorded pair was rounded inward to a multiple of G, so the bounds are the low
less G-1 and the high plus G-1.  A page whose rows are all null has no bounds
(lo and hi are None).
"""

CMP = frozenset(("ge", "le", "eq", "ne"))


def bounds(g, pg):
    """(lo, hi) of a page as written, or (None, None) when it has no bounds."""
    if pg.mn is None or pg.mx is None:
        return None, None
    if pg.exact:
        return pg.mn, pg.mx
    return pg.mn - (g - 1), pg.mx + (g - 1)


def sat(kind, cv, v):
    """Does value v (None for a null) satisfy the condition?"""
    if v is None:
        return kind == "nu"
    if kind == "ge":
        return v >= cv
    if kind == "le":
        return v <= cv
    if kind == "eq":
        return v == cv
    if kind == "ne":
        return v != cv
    return kind == "nn"


def settle(kind, cv, n, u, lo, hi):
    """What the header settles for every row of the page.

    1: the condition holds for all of them, 0: it fails for all of them,
    -1: the header settles nothing.
    """
    if lo is None:
        # every row is null
        return 1 if kind == "nu" else 0
    if kind == "nu":
        if u >= n:
            return 1
        return 0 if u == 0 else -1
    if kind == "nn":
        if u == 0:
            return 1
        return 0 if u >= n else -1
    if kind == "ge":
        if hi < cv:
            return 0
        return 1 if (u == 0 and lo >= cv) else -1
    if kind == "le":
        if lo > cv:
            return 0
        return 1 if (u == 0 and hi <= cv) else -1
    if kind == "eq":
        if cv < lo or cv > hi:
            return 0
        return 1 if (u == 0 and lo == hi) else -1
    # ne
    if lo == hi == cv:
        return 0
    return 1 if (u == 0 and (cv < lo or cv > hi)) else -1


def estimate(kind, cv, n, u, lo, hi):
    """The spread of the header: the count of the condition on an unread page."""
    if kind == "nu":
        return u
    if lo is None:
        return 0
    have = n - u
    if kind == "nn":
        return have
    width = hi - lo + 1
    if kind == "ge":
        part = hi - cv + 1
    elif kind == "le":
        part = cv - lo + 1
    else:
        part = 1 if lo <= cv <= hi else 0
    if part <= 0:
        return have if kind == "ne" else 0
    if part > width:
        part = width
    x = -(-have * part // width)
    return have - x if kind == "ne" else x


def exact(kind, cv, vals):
    """The count a read of a page yields: its values as written that satisfy."""
    if kind == "nu":
        return vals.count(None)
    if kind == "nn":
        return len(vals) - vals.count(None)
    t = 0
    if kind == "ge":
        for v in vals:
            if v is not None and v >= cv:
                t += 1
    elif kind == "le":
        for v in vals:
            if v is not None and v <= cv:
                t += 1
    elif kind == "eq":
        t = vals.count(cv)
    else:
        for v in vals:
            if v is not None and v != cv:
                t += 1
    return t
