# The same search carried over sets of keys instead of sets of cells. A group is
# grown by absorbing whole cells, a bar forbids a group holding both of its keys,
# and the cells the groups cover are read off at the end.
def span(bk, c):
    cells = bk.cells()
    seat = dict((i, frozenset(cells[i])) for i in sorted(cells))
    tags = [sorted(bk.tags[n]) for n in bk.open_tags()]
    bars = sorted(bk.bars)
    start = seat[c]
    seen = set()
    work = [start]
    wide = set(start)
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
                bigger = grp | seat[bk.find(k)]
                if any(a in bigger and b in bigger for a, b in bars):
                    continue
                work.append(bigger)
    return set(i for i in sorted(cells) if i != c and (seat[i] & wide))
