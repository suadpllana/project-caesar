def at(pool, span, r):
    tgt = r.plen if r.have == 0 else r.have
    if not r.seen:
        return 0
    return tgt - tgt % span
