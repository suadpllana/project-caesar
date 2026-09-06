def sq(h, r):
    out = []
    if r.n in h.rs:
        out.append(r.n)
    for n in h.op:
        if n in h.rs and n not in out:
            out.append(n)
    for n in h.sd.values():
        if n in h.rs and n not in out:
            out.append(n)
    return out


def fd(h, r, nm):
    for n in sq(h, r):
        if nm in h.rs[n].p.pv:
            return n
    return 0
