from kv import pool


def sink(kv):
    return -(-kv.a // kv.w)


def edge(kv, rq):
    n = rq.len()
    if n <= kv.s:
        return sink(kv)
    return max(sink(kv), (n - kv.s) // kv.w)


def trim(kv, rq):
    want = edge(kv, rq)
    while rq.up < want:
        pid = rq.pg.pop(rq.up, 0)
        if pid:
            pool.rest(kv, pid)
        rq.up += 1


def holds(kv, rq, i):
    if i < 0 or i >= rq.len():
        return 0
    return rq.pg.get(i // kv.w, 0)


def clear(kv, rq):
    for j in sorted(rq.pg):
        pool.rest(kv, rq.pg[j])
    rq.pg = {}
