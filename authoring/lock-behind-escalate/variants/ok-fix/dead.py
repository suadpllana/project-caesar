from lm import grant


def choose(held, wait):
    rel = grant.Relation(held, wait)
    cyclic = rel.cyclic()
    if not cyclic:
        return None
    best = None
    for txn in cyclic:
        key = (held.count(txn), -wait.req[txn][0])
        if best is None or key < best[0]:
            best = (key, txn)
    return best[1]
