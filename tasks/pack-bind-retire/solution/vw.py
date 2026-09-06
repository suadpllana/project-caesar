def mk(h, p):
    out = []
    seen = set()
    q = list(p.nd)
    while q:
        nm = q.pop(0)
        r = h.sr(nm)
        if r is None or r.n in seen:
            continue
        seen.add(r.n)
        out.append(r.n)
        q.extend(r.p.nd)
    return out


def sq(h, r):
    out = [r.n]
    seen = {r.n}
    for n in r.fx:
        if n in h.rs and n not in seen:
            seen.add(n)
            out.append(n)
    for n in h.op:
        if n in h.rs and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def fd(h, r, nm):
    for n in sq(h, r):
        if nm in h.rs[n].p.pv:
            return n
    return 0
