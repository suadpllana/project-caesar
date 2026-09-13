from pan import grid, seat


def bulk(p, n, lo, sp):
    for i in range(n):
        p.made += 1
        grid.put(p, p.n, grid.Nd(grid.draw(p), "k%d" % p.made, lo + (i % sp)))
    seat.hold(p)


def ins(p, k, rid, ln):
    grid.put(p, k, grid.Nd(grid.draw(p), rid, ln))
    seat.hold(p)


def dele(p, rid):
    nd = grid.row(p, rid)
    if nd is None:
        return
    k = grid.rank(p, nd)
    grid.drop(p, nd)
    if p.anc is nd:
        if p.n == 0:
            p.anc = None
            p.top = 0
        else:
            p.anc = grid.kth(p, k if k < p.n else p.n - 1)
    seat.hold(p)


def move(p, rid, k):
    nd = grid.row(p, rid)
    if nd is None:
        return
    hm = nd.hm
    grid.drop(p, nd)
    nd.l = nd.r = nd.up = None
    nd.sz = 1
    nd.hm = hm
    nd.ms = hm if hm is not None else 0
    nd.uc = 0 if hm is not None else 1
    grid.put(p, k, nd)
    seat.hold(p)


def rest(p, rid, ln):
    nd = grid.row(p, rid)
    if nd is None:
        return
    nd.ln = ln
    grid.wipe(p, nd)
    seat.hold(p)


def span(p, w):
    p.w = w
    grid.fresh(p)
    seat.hold(p)
