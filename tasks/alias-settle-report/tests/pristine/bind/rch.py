def span(bk, c, off):
    cells = bk.cells()
    seat = dict((i, set(ks)) for i, ks in cells.items())
    near = dict((i, set()) for i in seat)
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        hit = [i for i in seat if pool & seat[i]]
        if len(hit) > 1:
            for i in hit:
                near[i].update(hit)
    out = set()
    seen = set()
    work = [c]
    while work:
        i = work.pop()
        if i in seen:
            continue
        seen.add(i)
        for j in near[i]:
            out.add(j)
            work.append(j)
    out.discard(c)
    return out
