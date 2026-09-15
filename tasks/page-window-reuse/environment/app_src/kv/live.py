from kv import pool


def need(kv, rq, j):
    n = rq.len()
    if j * kv.w >= n:
        return False
    return (j + 1) * kv.w > n - kv.s


def trim(kv, rq):
    while rq.up in rq.pg and not need(kv, rq, rq.up):
        pool.rest(kv, rq.pg.pop(rq.up))
        rq.up += 1


def holds(kv, rq, i):
    if i < 0 or i >= rq.len():
        return 0
    return rq.pg.get(i // kv.w, 0)


def clear(kv, rq):
    for j in sorted(rq.pg):
        pool.rest(kv, rq.pg[j])
    rq.pg = {}
