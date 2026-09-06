def mk(h, p):
    seq = []
    q = list(p.nd)
    i = 0
    while i < len(q):
        nm = q[i]
        i += 1
        r = h.sr(nm)
        if r is None or r.n in seq:
            continue
        seq.append(r.n)
        q.extend(r.p.nd)
    return seq


def sq(h, r):
    out = [r.n]
    for n in list(r.fx) + list(h.op):
        if n in h.rs and n not in out:
            out.append(n)
    return out


def fd(h, r, nm):
    for n in sq(h, r):
        if nm in h.rs[n].p.pv:
            return n
    return 0
