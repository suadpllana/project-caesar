"""Which condition runs on which chunk next.

A condition and a chunk of its column are pending while the condition has not
been applied to that chunk and the chunk still holds a live row.  The pair
applied next has the smallest key, the smaller of the live rows the chunk
holds and the count of the condition on it; ties go to the condition written
earlier, then to the lower chunk.  The count of a condition on a chunk sums
its counts on the chunk's pages: exact on a page read so far, the spread of
the header otherwise.

Keys move as rows die (live counts) and as pages are read (counts), so the
pairs sit in a heap holding an entry at every pending pair's current key;
entries whose key is no longer current are skipped when they surface.
"""
from heapq import heapify, heappop, heappush

from scn import hdr, step


def _counts(mem, cd):
    c = cd.c
    kind = cd.kind
    v = cd.v
    pgs = mem.pgs[c]
    lo = mem.lo[c]
    hi = mem.hi[c]
    wv = mem.wv[c]
    first = mem.first[c]
    spread = hdr.spread
    exact = hdr.exact
    per = []
    for j in range(len(first) - 1):
        t = 0
        for pid in range(first[j], first[j + 1]):
            vals = wv[pid]
            if vals is None:
                pg = pgs[pid]
                t += spread(kind, v, pg.n, pg.nulls, lo[pid], hi[pid])
            else:
                t += exact(kind, v, vals)
        per.append(t)
    return per


def run(seg, q, st, out):
    mem = st.mem
    conds = q.conds
    live = st.live
    bycol = st.bycol
    same = {}
    cnt = []
    for cd in conds:
        sig = (cd.kind, cd.c, cd.v)
        per = same.get(sig)
        if per is None:
            per = _counts(mem, cd)
            same[sig] = per
        cnt.append(list(per))
    st.cnt = cnt
    heap = []
    cur = []
    done = []
    for pos, cd in enumerate(conds):
        lv = live[cd.c]
        per = cnt[pos]
        ks = [a if a < b else b for a, b in zip(lv, per)]
        cur.append(ks)
        done.append(bytearray(len(ks)))
        for j, k in enumerate(ks):
            if lv[j] > 0:
                heap.append((k, pos, j))
    heapify(heap)
    touch = st.touch
    apply = step.apply
    while heap:
        k, pos, j = heappop(heap)
        if done[pos][j] or cur[pos][j] != k:
            continue
        if live[conds[pos].c][j] <= 0:
            continue
        done[pos][j] = 1
        apply(st, pos, j, out)
        for c2, tj in touch.items():
            if not tj:
                continue
            lv2 = live[c2]
            ps = bycol[c2]
            for j2 in tj:
                n2 = lv2[j2]
                if n2 <= 0:
                    continue
                for pos2 in ps:
                    if done[pos2][j2]:
                        continue
                    x = cnt[pos2][j2]
                    nk = n2 if n2 < x else x
                    if nk != cur[pos2][j2]:
                        cur[pos2][j2] = nk
                        heappush(heap, (nk, pos2, j2))
            tj.clear()
