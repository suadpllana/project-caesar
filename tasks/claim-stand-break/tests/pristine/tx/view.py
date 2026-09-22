import bisect

from tx import hold


def under(txn, key):
    ix = txn.ci.get(key)
    if not ix:
        return hold.MISS
    return txn.cv[key][-1]


def one(st, txn, key, ver):
    val = under(txn, key)
    return st.at(key, ver) if val is hold.MISS else val


def many(st, txn, lo, hi, n, ver):
    got = []
    ck = txn.ck
    j = bisect.bisect_left(ck, lo)
    walk = st.span(lo, hi)
    ka = next(walk, None)
    while len(got) < n:
        kb = ck[j] if j < len(ck) and ck[j] <= hi else None
        if ka is None and kb is None:
            break
        if kb is None or (ka is not None and ka < kb):
            key = ka
            ka = next(walk, None)
        elif ka is None or kb < ka:
            key = kb
            j += 1
        else:
            key = ka
            ka = next(walk, None)
            j += 1
        val = one(st, txn, key, ver)
        if val is not None:
            got.append((key, val))
    return got
