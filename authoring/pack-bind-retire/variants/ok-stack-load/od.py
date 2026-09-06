def dp(h, nm):
    r = h.sr(nm)
    if r is None:
        return 0
    del h.sd[nm]
    if r.n in h.op:
        h.op.remove(r.n)
    return r.n


def od(ns):
    return sorted(ns, reverse=True)
