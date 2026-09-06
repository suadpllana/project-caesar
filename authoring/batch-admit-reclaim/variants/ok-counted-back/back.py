from eng.pool import keys


def at(pool, span, r):
    tgt = r.plen if r.have == 0 else r.have
    ks = keys(r.toks, span, tgt)
    lo, n = 0, 0
    while lo < len(ks) and pool.has(ks[lo]):
        n += 1
        lo += 1
    return n * span
