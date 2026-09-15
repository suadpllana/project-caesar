from kv import pool


def sink(kv):
    return -(-kv.a // kv.w)


def want(kv, rq):
    n = rq.len()
    top = -(-n // kv.w)
    keep = set(range(min(sink(kv), top)))
    lo = max(0, n - kv.s) // kv.w
    keep.update(range(lo, top))
    return keep


def trim(kv, rq):
    if not rq.pg:
        return
    stay = want(kv, rq)
    for j in sorted(rq.pg):
        if j not in stay:
            pool.rest(kv, rq.pg.pop(j))


def holds(kv, rq, i):
    if i < 0 or i >= rq.len():
        return 0
    return rq.pg.get(i // kv.w, 0)


def clear(kv, rq):
    for j in sorted(rq.pg):
        pool.rest(kv, rq.pg[j])
    rq.pg = {}
