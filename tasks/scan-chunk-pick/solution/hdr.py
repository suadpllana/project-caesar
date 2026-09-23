"""What a page header proves, and the estimate the order is chosen on.

A page header carries a row count, a null count, a recorded low and high with a flag saying
whether that pair is exact, and the sum of the non-null values. When the flag is off the
recorded pair was rounded inward to a multiple of the segment granularity, so the usable bounds
are the recorded ones pushed out by g - 1. Reading them as exact skips pages that hold matches.

`miss` and `allsat` are the two sound tests: the bounds and the null count prove that no row of
the page matches, or that every row does. A null satisfies is-null and nothing else, so a page
holding a null never passes a comparison or is-not-null whole. `pinned` says when the header
alone fixes every value the page holds: every row null, or no nulls and a low equal to its high
after widening. `guess` is neither: it is the interpolation the order is chosen on, spreading
the non-null rows evenly over the bounds, and it is allowed to be wrong.
"""


def bounds(seg, pg):
    if pg.mn is None:
        return None
    if pg.exact:
        return pg.mn, pg.mx
    w = seg.g - 1
    return pg.mn - w, pg.mx + w


def miss(seg, pg, cond):
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
    k = cond.kind
    if k == "nu":
        return pg.nulls == pg.n
    if pg.nulls:
        return False
    if k == "nn":
        return True
    lo, hi = bounds(seg, pg)
    v = cond.v
    if k == "ge":
        return lo >= v
    if k == "le":
        return hi <= v
    if k == "eq":
        return lo == hi == v
    return hi < v or lo > v


def pinned(seg, pg):
    if pg.nulls == pg.n:
        return True, None
    if pg.nulls:
        return False, None
    lo, hi = bounds(seg, pg)
    if lo == hi:
        return True, lo
    return False, None


def guess(seg, pg, cond):
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
