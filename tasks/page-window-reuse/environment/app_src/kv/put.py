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
        keep.add(kv, pid)
    return True
