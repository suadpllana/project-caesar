# The same search, walking its frontier oldest first and keeping the groups it
# has already opened in a list rather than a set. Same answer, different order.
def span(bk, c, off):
    cells = bk.cells()
    ids = sorted(i for i in cells if not (set(cells[i]) & off))
    seat = dict((i, set(cells[i])) for i in ids)
    near = dict((i, set()) for i in ids)
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        if pool & off:
            continue
        hit = [i for i in ids if pool & seat[i]]
        for i in hit:
            near[i].update(j for j in hit if j != i)
    stop = set()
    for a, b in bk.bars:
        ra, rb = bk.find(a), bk.find(b)
        if ra != rb:
            stop.add((min(ra, rb), max(ra, rb)))
    line = [frozenset((c,))]
    done = []
    at = 0
    out = set()
    while at < len(line):
        grp = line[at]
        at += 1
        if grp in done:
            continue
        done.append(grp)
        out |= grp
        for i in sorted(grp):
            for j in sorted(near[i]):
                if j in grp:
                    continue
                if any((min(k, j), max(k, j)) in stop for k in grp):
                    continue
                wider = grp | {j}
                if wider not in line:
                    line.append(wider)
    out.discard(c)
    return out
