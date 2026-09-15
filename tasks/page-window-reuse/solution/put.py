"""Writing one token, and what happens when a page completes.

A page takes its place under the page before it as soon as it is made, but it cannot be
reused while it is still being written. The moment it is full its tokens are known, so it
either becomes reusable or finds that the same tokens already sit below the same page - in
which case the request hands its own page straight back to the pool and takes the one that
is already there.
"""
from kv import keep, pool, store


def write(kv, rq, token):
    w = kv.w
    n = rq.len()
    j = n // w
    off = n - j * w
    if off == 0:
        pid = pool.grab(kv)
        if not pid:
            return False
        pg = store.Pg(rq.pg[j - 1] if j else 0, w)
        kv.pg[pid] = pg
        kv.ref[pid] = 1
        keep.join(kv, pid, pg.prev)
        rq.pg[j] = pid
    else:
        pid = rq.pg[j]
        pg = kv.pg[pid]
    pg.tokens[off] = token
    pg.n = off + 1
    if pg.n == w:
        had = keep.find(kv, pg.prev, tuple(pg.tokens))
        if had:
            pool.loose(kv, pid)
            pool.hold(kv, had)
            rq.pg[j] = had
        else:
            keep.add(kv, pid)
    return True
