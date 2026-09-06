from eng.pool import keys


def at(pool, span, r):
    tgt = r.plen if r.have == 0 else r.have
    n = 0
    for k in keys(r.toks, span, tgt):
        if not pool.has(k):
            break
        n += 1
    return n * span
