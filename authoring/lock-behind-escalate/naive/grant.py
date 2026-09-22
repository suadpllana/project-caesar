from lm import spec

LATEST = 1 << 60


def compat(a, b):
    return a == "s" and b == "s"


def overlap(a, b):
    return a == b or spec.table_of(a) == b or spec.table_of(b) == a


def clash(tgt, mode, tgt2, mode2):
    return overlap(tgt, tgt2) and not compat(mode, mode2)


def waits_on(held, wait, req):
    seen = set()
    for u in held.clashers(req.txn, req.tgt, req.mode):
        if u not in seen:
            seen.add(u)
            yield u
    for w in wait.on(spec.table_of(req.tgt)):
        if w.txn != req.txn and w.seq < req.seq and w.txn not in seen \
                and clash(req.tgt, req.mode, w.tgt, w.mode):
            seen.add(w.txn)
            yield w.txn


def depends(held, wait, v, txn):
    seen = {v}
    todo = [v]
    while todo:
        req = wait.of.get(todo.pop())
        if req is None:
            continue
        for u in waits_on(held, wait, req):
            if u == txn:
                return True
            if u not in seen:
                seen.add(u)
                todo.append(u)
    return False


def grantable(held, wait, txn, tgt, mode, seq):
    for _u in held.clashers(txn, tgt, mode):
        return False
    for w in wait.on(spec.table_of(tgt)):
        if w.txn == txn or w.seq >= seq or not clash(tgt, mode, w.tgt, w.mode):
            continue
        if not depends(held, wait, w.txn, txn):
            return False
    return True
