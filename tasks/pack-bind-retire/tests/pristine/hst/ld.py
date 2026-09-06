from hst import bd


def ld(h, nm, md):
    if h.sr(nm) is not None:
        return []
    made = []
    seen = []
    q = [nm]
    while q:
        x = q.pop(0)
        if x in seen:
            continue
        seen.append(x)
        q.extend(h.pk[x].nd)
    for x in seen:
        if h.sr(x) is not None:
            continue
        p = h.pk[x]
        r = h.mk(p)
        h.sd[x] = r.n
        made.append(r.n)
        if md == "open" and x == nm:
            h.op.append(r.n)
        for s in p.st:
            bd.us(h, r, s)
    return made
