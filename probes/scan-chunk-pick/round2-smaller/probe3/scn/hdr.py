def bounds(seg, ch):
    if ch.mn is None:
        return None, None
    if ch.exact:
        return ch.mn, ch.mx
    g = seg.g
    return ch.mn - (g - 1), ch.mx + (g - 1)


def miss(seg, ch, cond):
    k = cond.kind
    if k == "nu":
        return ch.nulls == 0
    have = ch.n - ch.nulls
    if have == 0 or k == "nn":
        return have == 0
    lo, hi = bounds(seg, ch)
    v = cond.v
    if k == "ge":
        return hi < v
    if k == "le":
        return lo > v
    if k == "eq":
        return v < lo or v > hi
    return lo == hi == v


def allsat(seg, ch, cond):
    k = cond.kind
    if k == "nu":
        return ch.nulls == ch.n
    if k == "nn":
        return ch.nulls == 0
    if ch.nulls != 0:
        # A null never satisfies a comparison, so a chunk holding any
        # null can never have a comparison hold for every row it has.
        return False
    lo, hi = bounds(seg, ch)
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


def guess(seg, ch, cond):
    k = cond.kind
    if k == "nu":
        return ch.nulls
    have = ch.n - ch.nulls
    if have == 0 or k == "nn":
        return have
    lo, hi = bounds(seg, ch)
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


def fixed_const(seg, ch):
    """Whether the header alone pins down every row this chunk holds.

    Returns (True, None) when every row is null, (True, v) when every
    row holds exactly v (no nulls), or (False, None) when the header
    does not settle it.
    """
    if ch.nulls == ch.n:
        return True, None
    if ch.nulls == 0:
        lo, hi = bounds(seg, ch)
        if lo is not None and lo == hi:
            return True, lo
    return False, None
