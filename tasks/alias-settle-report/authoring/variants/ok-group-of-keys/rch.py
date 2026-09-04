# The same search carried over sets of keys instead of sets of cells. A group is
# grown by absorbing whole cells, a bar forbids a group holding both of its keys,
# and the cells the groups cover are read off at the end. A cell that has gone is
# never absorbed and never reported.
def span(bk, c, off):
    cells = bk.cells()
    seat = dict((i, frozenset(cells[i])) for i in sorted(cells))
    here = sorted(i for i in cells if not (seat[i] & off))
    tags = [sorted(bk.tags[n]) for n in bk.open_tags()
            if not (set(bk.tags[n]) & off)]
    bars = sorted(bk.bars)
    seen = set()
    work = [seat[c]]
    wide = set(seat[c])
    while work:
        grp = work.pop()
        if grp in seen:
            continue
        seen.add(grp)
        wide |= grp
        for pool in tags:
            if not (set(pool) & grp):
                continue
            for k in pool:
                if k in grp:
                    continue
                nxt = seat[bk.find(k)]
                if nxt & off:
                    continue
                bigger = grp | nxt
                if any(a in bigger and b in bigger for a, b in bars):
                    continue
                work.append(bigger)
    return set(i for i in here if i != c and (seat[i] & wide))
