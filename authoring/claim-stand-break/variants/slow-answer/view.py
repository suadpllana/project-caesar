"""Answering a read.

Two states go into every answer and they move independently. The rows come from the version
the transaction opened at, which never moves. The cover comes from the transaction's own
changes, and only those made before the read: a change made after a read never changed what
that read returned, and a change taken back by a rollback stops covering the key it was over,
which is why the cover is asked for at a claim index rather than taken as it stands.

A scan merges two key orders, the keys the store has ever held and the keys this transaction
has changed, because a key the transaction has just made exists for it and for nobody else.
"""
import bisect

from tx import hold


def under(txn, key, upto):
    """The value of the last standing change to key made before claim index upto."""
    ix = txn.ci.get(key)
    if not ix:
        return hold.MISS
    j = bisect.bisect_left(ix, upto)
    if not j:
        return hold.MISS
    return txn.cv[key][j - 1]


def one(st, txn, key, upto, ver):
    """What key answers for this transaction, at claim index upto, against version ver."""
    val = under(txn, key, upto)
    return st.at(key, ver) if val is hold.MISS else val


def many(st, txn, lo, hi, n, upto, ver):
    """The first n rows from lo to hi in key order."""
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
        val = one(st, txn, key, upto, ver)
        if val is not None:
            got.append((key, val))
    return got
