# Which cells could still end up welded to this one, given what has already left
# the desk.
#
# The question is never "what is joined now" but "what could a still-open tag
# join later", so the answer is worked out over the tags that have not shut. A
# tag speaks about every key in its pool, so any two cells it touches are one
# declaration apart, and a chain of such declarations reaches further still.
#
# A tag is handed its pool once. The moment any key of that pool is filed the
# pool is stale and the tag says nothing further, so a tag is asked about only
# while every key it names is still here. That is also what takes a filed cell
# out of the graph: every tag that could have reached it named one of its keys,
# so once it goes nothing can reach it and nothing can reach through it, and no
# separate striking-out is needed.
#
# The chain is not free either. Welding a chain welds everything on it into one
# cell, and a bar standing between any two of those cells says that cell can
# never exist. So a route counts only when the whole group it would create is
# clear of bars - not merely its ends, and not merely its consecutive steps.
# That is why this is a search over growing groups rather than a walk over
# edges: the group is what a bar forbids.
def span(bk, c, off):
    cells = bk.cells()
    seat = dict((i, set(ks)) for i, ks in cells.items())
    ids = sorted(seat)
    near = dict((i, set()) for i in ids)
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        if pool & off:
            continue
        hit = [i for i in ids if pool & seat[i]]
        if len(hit) > 1:
            for i in hit:
                near[i].update(hit)
    for i in ids:
        near[i].discard(i)
    if not bk.bars:
        seen = {c}
        work = [c]
        while work:
            i = work.pop()
            for j in near[i] - seen:
                seen.add(j)
                work.append(j)
        seen.discard(c)
        return seen
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
