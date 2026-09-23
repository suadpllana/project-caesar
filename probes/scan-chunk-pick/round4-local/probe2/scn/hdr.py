"""What a page header proves, and what it lets a count be estimated at.

A header knows two things: how many of the page's rows are null, and that
every other value lies between its bounds.  Under ``e`` the bounds are the
recorded pair; under ``w`` the recorded pair was rounded inward to a multiple
of G, so the bounds are widened by G-1 on each side.  An all-null page has no
bounds.
"""

from bisect import bisect_left, bisect_right

COMPARE = ("ge", "le", "eq", "ne")


def bounds(g, pg):
    """Effective (low, high) bounds of a page, or (None, None) when it has none."""
    if pg.mn is None or pg.mx is None:
        return None, None
    if pg.exact:
        return pg.mn, pg.mx
    return pg.mn - (g - 1), pg.mx + (g - 1)


def verdict(kind, v, n, u, lo, hi):
    """1 when the header proves the condition holds for every row the page
    holds, -1 when it proves it fails for every one, 0 when it settles nothing."""
    if kind == "nu":
        if u == n:
            return 1
        if u == 0:
            return -1
        return 0
    if kind == "nn":
        if u == 0:
            return 1
        if u == n:
            return -1
        return 0
    # A comparison: a null satisfies none of them.
    if u == n:
        return -1
    if lo is None:
        return 0
    if kind == "ge":
        if hi < v:
            return -1
        if u == 0 and lo >= v:
            return 1
        return 0
    if kind == "le":
        if lo > v:
            return -1
        if u == 0 and hi <= v:
            return 1
        return 0
    if kind == "eq":
        if v < lo or v > hi:
            return -1
        if u == 0 and lo == hi == v:
            return 1
        return 0
    # ne
    if lo == hi == v:
        return -1
    if u == 0 and (v < lo or v > hi):
        return 1
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
    if part > width:
        part = width
    got = -(-(have * part) // width)
    return have - got if kind == "ne" else got


def exact_sorted(kind, v, sv, nulls):
    """The count of a condition over a page as written, from its non-null
    values in ascending order and its number of nulls."""
    if kind == "nu":
        return nulls
    if kind == "nn":
        return len(sv)
    if kind == "ge":
        return len(sv) - bisect_left(sv, v)
    if kind == "le":
        return bisect_right(sv, v)
    same = bisect_right(sv, v) - bisect_left(sv, v)
    if kind == "eq":
        return same
    return len(sv) - same


def test(kind, v):
    """A predicate telling whether a value (None for null) satisfies a condition."""
    if kind == "nu":
        return lambda x: x is None
    if kind == "nn":
        return lambda x: x is not None
    if kind == "ge":
        return lambda x: x is not None and x >= v
    if kind == "le":
        return lambda x: x is not None and x <= v
    if kind == "eq":
        return lambda x: x is not None and x == v
    return lambda x: x is not None and x != v


def verdicts(kind, v, ns, us, los, his):
    """``verdict`` for every page of a column at once (lists of n, u, low, high)."""
    if kind == "nu":
        return [1 if u == n else (-1 if u == 0 else 0) for n, u in zip(ns, us)]
    if kind == "nn":
        return [1 if u == 0 else (-1 if u == n else 0) for n, u in zip(ns, us)]
    rows = zip(ns, us, los, his)
    if kind == "ge":
        return [-1 if u == n else (0 if lo is None else (
            -1 if hi < v else (1 if u == 0 and lo >= v else 0)))
            for n, u, lo, hi in rows]
    if kind == "le":
        return [-1 if u == n else (0 if lo is None else (
            -1 if lo > v else (1 if u == 0 and hi <= v else 0)))
            for n, u, lo, hi in rows]
    if kind == "eq":
        return [-1 if u == n else (0 if lo is None else (
            -1 if (v < lo or v > hi) else (1 if u == 0 and lo == v and hi == v else 0)))
            for n, u, lo, hi in rows]
    return [-1 if u == n else (0 if lo is None else (
        -1 if (lo == v and hi == v) else (1 if u == 0 and (v < lo or v > hi) else 0)))
        for n, u, lo, hi in rows]


def spreads(kind, v, ns, us, los, his):
    """``spread`` for every page of a column at once."""
    if kind == "nu":
        return list(us)
    rows = zip(ns, us, los, his)
    if kind == "nn":
        return [0 if lo is None else n - u for n, u, lo, hi in rows]
    if kind == "ge":
        return [0 if (lo is None or v > hi) else (
            n - u if v <= lo else -(-((n - u) * (hi - v + 1)) // (hi - lo + 1)))
            for n, u, lo, hi in rows]
    if kind == "le":
        return [0 if (lo is None or v < lo) else (
            n - u if v >= hi else -(-((n - u) * (v - lo + 1)) // (hi - lo + 1)))
            for n, u, lo, hi in rows]
    if kind == "eq":
        return [0 if (lo is None or v < lo or v > hi) else -(-(n - u) // (hi - lo + 1))
                for n, u, lo, hi in rows]
    return [0 if lo is None else (
        n - u if (v < lo or v > hi) else (n - u) - -(-(n - u) // (hi - lo + 1)))
        for n, u, lo, hi in rows]
