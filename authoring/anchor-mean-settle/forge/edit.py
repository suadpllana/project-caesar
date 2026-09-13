from pan import grid


def bulk(p, n, lo, sp):
    grid.note("bulk %d %d %d" % (n, lo, sp))
    for i in range(n):
        p.made += 1
        p.rows.append(grid.Row("k%d" % p.made, lo + (i % sp)))


def ins(p, k, rid, ln):
    grid.note("ins %d %s %d" % (k, rid, ln))
    p.rows.insert(k, grid.Row(rid, ln))


def dele(p, rid):
    grid.note("del %s" % rid)
    p.rows[:] = [r for r in p.rows if r.rid != rid]


def move(p, rid, k):
    grid.note("move %s %d" % (rid, k))
    for i, r in enumerate(p.rows):
        if r.rid == rid:
            p.rows.insert(k, p.rows.pop(i))
            return


def rest(p, rid, ln):
    grid.note("set %s %d" % (rid, ln))
    for r in p.rows:
        if r.rid == rid:
            r.ln = ln


def span(p, w):
    grid.note("span %d" % w)
    p.w = w
