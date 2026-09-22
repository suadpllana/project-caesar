"""Header-only decisions, and the estimate the order is chosen on.

Every chunk carries a row count, a null count, a recorded low and high and a flag saying
whether that pair is exact. When it is not, the recorded pair was rounded inward to a multiple
of the segment granularity, so the usable bounds are the recorded ones pushed out by g - 1.
Reading them as exact skips chunks that hold matches.

`miss` and `allsat` are the two sound tests: the header proves no row of the chunk matches, or
that every row does. Both fail on a chunk holding nulls for every condition but is-null. A
widened pair is always a wider one, so low == high proves the whole chunk carries one value
whatever the flag says.
`pinned` says whether the header alone fixes the value every row of the chunk holds as
written: every row null, or no nulls and a low equal to its high. The report pass needs no read
for such a chunk.
`guess` is neither - it is the interpolation the order is chosen on, spreading the live rows
evenly over the bounds, and it is allowed to be wrong.
"""


def bounds(seg, ch):
    if ch.mn is None:
        return None
    if ch.exact:
        return ch.mn, ch.mx
    w = seg.g - 1
    return ch.mn - w, ch.mx + w


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
    if ch.nulls:
        return False
    if k == "nn":
        return True
    lo, hi = bounds(seg, ch)
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


def pinned(seg, ch):
    if ch.nulls == ch.n:
        return True, None
    if ch.nulls:
        return False, None
    lo, hi = bounds(seg, ch)
    if lo == hi:
        return True, lo
    return False, None
