"""Which condition is applied to which chunk, and when.

A condition and a chunk of its column are a pending pair while the condition
has not been applied to that chunk and the chunk still holds a live row.  The
pair applied next is the one expected to leave the fewest rows alive: the
smaller of the live rows the chunk holds and the count of the condition on it.
A tie goes to the condition written earlier, then to the lower chunk.

The count of a condition on a chunk is the sum of its counts on the pages of
the chunk: exact over the page as written once the page has been read (from
the start of the query if it was read before), the spread of the header
otherwise.  Pending pairs sit in a heap keyed (expected rows, condition,
chunk).  A pair's key changes only when a chunk loses live rows or one of its
pages is read; a new entry is pushed then, and an entry whose key is no
longer the pair's current one is dropped when it surfaces.
"""
from heapq import heapify, heappop, heappush

from scn import hdr, live, step


def counts(seg, mem, c, group):
    """The count of every condition in group, all on column c, on every
    chunk of the column at the start of the query."""
    known = mem.vals
    spread = hdr.spread
    exact = hdr.exact
    specs = [(cd.kind, cd.v) for cd in group]
    per = [[] for _ in group]
    width = range(len(group))
    whole = mem.cval
    for ch, bnds in zip(seg.cols[c], hdr.table(mem, c)):
        j = ch.j
        if (c, j) in whole:
            d = live.chunk_digest(mem, (c, j))
            for i in width:
                k, v = specs[i]
                per[i].append(exact(d, k, v))
            continue
        tots = [0] * len(group)
        for pg, b in zip(ch.pages, bnds):
            key = (c, j, pg.p)
            if key in known:
                d = live.digest(mem, key)
                for i in width:
                    k, v = specs[i]
                    tots[i] += exact(d, k, v)
            else:
                u = pg.nulls
                n = pg.n
                for i in width:
                    k, v = specs[i]
                    tots[i] += spread(k, v, u, n, b)
        for i in width:
            per[i].append(tots[i])
    return per


def run(seg, q, st, out):
    conds = q.conds
    mem = st.mem
    bycol = {}
    for cd in conds:
        bycol.setdefault(cd.c, []).append(cd)
    lcs = {}
    cnt = [None] * len(conds)
    for c, group in bycol.items():
        lcs[c] = live.track(st, c)
        for cd, per in zip(group, counts(seg, mem, c, group)):
            cnt[cd.pos] = per

    done = [bytearray(len(seg.cols[cd.c])) for cd in conds]
    cur = []
    heap = []
    for cd in conds:
        pos = cd.pos
        per = cnt[pos]
        now = []
        for j, n in enumerate(lcs[cd.c]):
            k = per[j]
            key = n if n < k else k
            now.append(key)
            if n > 0:
                heap.append((key, pos, j))
        cur.append(now)
    heapify(heap)

    dirty = st.dirty
    dirty.clear()
    while heap:
        key, pos, j = heappop(heap)
        if done[pos][j] or cur[pos][j] != key:
            continue
        cd = conds[pos]
        c = cd.c
        if lcs[c][j] <= 0:
            continue
        done[pos][j] = 1
        ch = seg.cols[c][j]
        fresh = step.apply(seg, st, cd, ch, out)
        if fresh:
            bnds = hdr.table(mem, c)[j]
            for pg in fresh:
                d = live.digest(mem, (c, j, pg.p))
                b = bnds[pg.p]
                for other in bycol[c]:
                    ok = other.kind
                    ov = other.v
                    cnt[other.pos][j] += (hdr.exact(d, ok, ov)
                                          - hdr.spread(ok, ov, pg.nulls, pg.n, b))
            dirty.add((c, j))
        for c2, j2 in dirty:
            n2 = lcs[c2][j2]
            if n2 <= 0:
                continue
            for other in bycol[c2]:
                p2 = other.pos
                if done[p2][j2]:
                    continue
                k2 = cnt[p2][j2]
                if n2 < k2:
                    k2 = n2
                if cur[p2][j2] != k2:
                    cur[p2][j2] = k2
                    heappush(heap, (k2, p2, j2))
        dirty.clear()
