from hst import bd, vw


def ld(h, nm, md):
    made = []
    br(h, nm, md, made)
    return made


def br(h, nm, md, made):
    r = h.sr(nm)
    if r is not None:
        if md == "open" and r.n not in h.op:
            h.op.append(r.n)
        return
    p = h.pk[nm]
    for d in p.nd:
        br(h, d, "own", made)
    fx = vw.mk(h, p)
    r = h.mk(p)
    r.fx = fx
    h.sd[nm] = r.n
    made.append(r.n)
    if md == "open":
        h.op.append(r.n)
    for s in p.st:
        bd.us(h, r, s)
