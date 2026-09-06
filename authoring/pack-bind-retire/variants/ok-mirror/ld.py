from hst import bd, vw


def ld(h, nm, md):
    fresh = []
    walk(h, nm, md, fresh)
    return fresh


def walk(h, nm, md, fresh):
    r = h.sr(nm)
    if r is not None:
        if md == "open" and r.n not in h.op:
            h.op.append(r.n)
        return
    p = h.pk[nm]
    for d in p.nd:
        walk(h, d, "own", fresh)
    fx = vw.build(h, p)
    r = h.mk(p)
    r.zz = fx
    h.sd[nm] = r.n
    fresh.append(r.n)
    if md == "open":
        h.op.append(r.n)
    for s in p.st:
        bd.us(h, r, s)
