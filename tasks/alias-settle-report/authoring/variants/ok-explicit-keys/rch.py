# Which cells could still end up welded to this one, given what has already left
# the desk.
#
# The question is never "what is joined now" but "what could a still-open tag
# join later", so the answer is worked out over the tags that have not shut. A
# tag speaks about every key in its pool, so any two cells it touches are one
# declaration apart, and a chain of such declarations reaches further still.
#
# A cell whose keys have gone is not there to be welded and is not there to be
# welded through, so it leaves the graph entirely rather than merely leaving the
# answer. Nothing else has to be struck out with it: a gone key sits only in a
# cell that has gone, so a pool that still names it touches nothing that is left.
#
# The chain is not free either. Welding a chain welds everything on it into one
# cell, and a bar standing between any two of those cells says that cell can
# never exist. So a route counts only when the whole group it would create is
# clear of bars - not merely its ends, and not merely its consecutive steps.
# That is why this is a search over growing groups rather than a walk over
# edges: the group is what a bar forbids.
def span(bk, c, off):
    cells = bk.cells()
    live = dict((i, set(ks)) for i, ks in cells.items() if not (set(ks) & off))
    ids = sorted(live)
    near = dict((i, set()) for i in ids)
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        hit = [i for i in ids if pool & live[i]]
        if len(hit) > 1:
            for i in hit:
                near[i].update(hit)
    for i in ids:
        near[i].discard(i)
    stop = set()
    for a, b in bk.bars:
        ra, rb = bk.find(a), bk.find(b)
        if ra != rb:
            stop.add((min(ra, rb), max(ra, rb)))
    out = set()
    seen = set()
    work = [frozenset((c,))]
    while work:
        grp = work.pop()
        if grp in seen:
            continue
        seen.add(grp)
        out |= grp
        rim = set()
        for i in grp:
            rim |= near[i]
        for j in rim - grp:
            if all((min(i, j), max(i, j)) not in stop for i in grp):
                work.append(grp | {j})
    out.discard(c)
    return out
