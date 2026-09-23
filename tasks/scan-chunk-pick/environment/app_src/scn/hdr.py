def stats(seg, ch):
    n = 0
    nulls = 0
    lo = None
    hi = None
    for pg in ch.pages:
        n += pg.n
        nulls += pg.nulls
        if pg.mn is not None:
            lo = pg.mn if lo is None or pg.mn < lo else lo
            hi = pg.mx if hi is None or pg.mx > hi else hi
    return n, nulls, lo, hi


def miss(seg, ch, cond):
    n, nulls, lo, hi = stats(seg, ch)
    k = cond.kind
    if k == "nu":
        return nulls == 0
    have = n - nulls
    if have == 0 or k == "nn":
        return have == 0
    v = cond.v
    if k == "ge":
        return hi < v
    if k == "le":
        return lo > v
    if k == "eq":
        return v < lo or v > hi
    return lo == hi == v


def allsat(seg, ch, cond):
    n, nulls, lo, hi = stats(seg, ch)
    k = cond.kind
    if k == "nu":
        return nulls == n
    if k == "nn":
        return nulls == 0
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
    n, nulls, lo, hi = stats(seg, ch)
    k = cond.kind
    if k == "nu":
        return nulls
    have = n - nulls
    if have == 0 or k == "nn":
        return have
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
