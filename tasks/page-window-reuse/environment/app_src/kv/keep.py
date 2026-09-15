from kv import pool


def start(kv):
    kv.ix = {}
    kv.mark = {}


def chain(prev, tokens):
    return hash((prev, tokens))


def join(kv, pid, prev):
    kv.mark[pid] = chain(kv.mark.get(prev, 0), None)


def add(kv, pid):
    pg = kv.pg[pid]
    key = chain(kv.mark.get(pg.prev, 0), tuple(pg.tokens))
    kv.mark[pid] = key
    kv.ix[key] = pid


def cut(kv, pid):
    key = kv.mark.pop(pid, None)
    if key is not None and kv.ix.get(key) == pid:
        del kv.ix[key]


def walk(kv, rq):
    w = kv.w
    prev = 0
    j = 0
    while (j + 1) * w <= len(rq.prompt):
        pid = kv.ix.get(chain(kv.mark.get(prev, 0), tuple(rq.prompt[j * w:(j + 1) * w])), 0)
        if not pid:
            break
        pool.hold(kv, pid)
        rq.pg[j] = pid
        prev = pid
        j += 1
    return j
