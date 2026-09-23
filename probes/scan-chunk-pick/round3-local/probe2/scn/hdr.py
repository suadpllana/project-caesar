"""What a page header knows about the page as written, and the counts of a
condition on a page.

A header knows three facts: `nulls` of its `n` rows are null, every other
value lies between its bounds, and those values sum to `sum`.  Under `e` the
bounds are the recorded pair; under `w` the recorded pair was rounded inward
to a multiple of G, so the bounds are widened by G-1 on each side.  A page
whose rows are all null has no bounds.
"""
from bisect import bisect_left, bisect_right


def bounds(seg, pg):
    """(low, high) of the page, or None when it has no bounds."""
    if pg.nulls >= pg.n or pg.mn is None or pg.mx is None:
        return None
    if pg.exact:
        return pg.mn, pg.mx
    w = seg.g - 1
    return pg.mn - w, pg.mx + w


def table(mem, c):
    """Bounds of every page of column c, per chunk, computed once per file."""
    t = mem.bnd.get(c)
    if t is None:
        seg = mem.seg
        t = [[bounds(seg, pg) for pg in ch.pages] for ch in seg.cols[c]]
        mem.bnd[c] = t
    return t


def settle(k, v, u, n, b):
    """What the first two facts prove about every row the page holds for the
    condition `k v`: True when it holds for all of them, False when it fails
    for all of them, None when the header cannot tell.  u and n are the nulls
    and rows of the page, b its bounds."""
    if u >= n:
        return k == "nu"
    if k == "nu":
        return False if u == 0 else None
    if k == "nn":
        return True if u == 0 else None
    if b is None:
        return None
    lo, hi = b
    if k == "ge":
        if hi < v:
            return False
        ok = lo >= v
    elif k == "le":
        if lo > v:
            return False
        ok = hi <= v
    elif k == "eq":
        if v < lo or v > hi:
            return False
        ok = lo == hi
    else:
        if lo == hi == v:
            return False
        ok = v < lo or v > hi
    return True if ok and u == 0 else None


def spread(k, v, u, n, b):
    """The count of the condition `k v` on a page that has not been read."""
    if k == "nu":
        return u
    if b is None:
        return 0
    have = n - u
    if k == "nn":
        return have
    lo, hi = b
    width = hi - lo + 1
    if k == "ge":
        part = hi - v + 1
    elif k == "le":
        part = v - lo + 1
    else:
        part = 1 if lo <= v <= hi else 0
    if part <= 0:
        return have if k == "ne" else 0
    if part > width:
        part = width
    got = -(-have * part // width)
    return have - got if k == "ne" else got


def digest(vals):
    """What a count needs of a page read: its non-null values in order and
    how many nulls it holds, as written."""
    have = sorted(x for x in vals if x is not None)
    return have, len(vals) - len(have)


def exact(d, k, v):
    """The count of the condition `k v` over a page as written, from its
    digest."""
    have, nulls = d
    if k == "nu":
        return nulls
    if k == "nn":
        return len(have)
    if k == "ge":
        return len(have) - bisect_left(have, v)
    if k == "le":
        return bisect_right(have, v)
    eq = bisect_right(have, v) - bisect_left(have, v)
    return eq if k == "eq" else len(have) - eq


def true_of(pg, b, vals):
    """True when the first two facts of the header hold of the values the
    page was written with, so that nothing the header settles can differ
    from what those values say."""
    have = [x for x in vals if x is not None]
    if len(vals) - len(have) != pg.nulls:
        return False
    if not have:
        return True
    return b is not None and b[0] <= min(have) and max(have) <= b[1]


def answer(pg, b, k):
    """(non-null count, sum) of the k live rows taking their value from the
    page, when the header alone answers it: every row of the page is null,
    the page holds no null and its bounds are one value, or those rows are
    every row of the page.  None otherwise."""
    u = pg.nulls
    if u >= pg.n:
        return 0, 0
    if u == 0 and b is not None and b[0] == b[1]:
        return k, k * b[0]
    if k == pg.n:
        return pg.n - u, pg.sum
    return None
