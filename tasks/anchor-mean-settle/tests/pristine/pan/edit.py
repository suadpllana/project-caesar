from pan import grid


def bulk(p, n, lo, sp):
    for i in range(n):
        p.made += 1
        p.rows.append(grid.Row("k%d" % p.made, lo + (i % sp)))


def ins(p, k, rid, ln):
    p.rows.insert(k, grid.Row(rid, ln))


def dele(p, rid):
    k = grid.find(p, rid)
    if k < 0:
        return
    del p.rows[k]
    if p.anc >= len(p.rows):
        p.anc = len(p.rows) - 1


def move(p, rid, k):
    i = grid.find(p, rid)
    if i < 0:
        return
    r = p.rows.pop(i)
    p.rows.insert(k, grid.Row(r.rid, r.ln))


def rest(p, rid, ln):
    k = grid.find(p, rid)
    if k < 0:
        return
    p.rows[k].ln = ln


def span(p, w):
    p.w = w
