"""Correct variant: a heap whose entries carry a stamp, and a stamp that goes stale is skipped."""
import heapq

from scn import hdr, live, step


def run(seg, q, st, out):
    stamp = {}
    heap = []

    def push(cd, j):
        if j in st.done[cd.pos]:
            return
        have = live.count(st, cd.c, j)
        if have <= 0:
            return
        got = st.hit.get((cd.c, j, cd.pos))
        b = hdr.guess(seg, seg.cols[cd.c][j], cd) if got is None else got
        key = (cd.pos, j)
        stamp[key] = stamp.get(key, 0) + 1
        heapq.heappush(heap, (min(have, b), cd.pos, j, stamp[key]))

    on = {}
    for cd in q.conds:
        on.setdefault(cd.c, []).append(cd)
        for ch in seg.cols[cd.c]:
            push(cd, ch.j)
    st.dirty.clear()
    while heap:
        _s, pos, j, mark = heapq.heappop(heap)
        if stamp.get((pos, j)) != mark or j in st.done[pos]:
            continue
        cd = q.conds[pos]
        step.decide(seg, q, st, cd, j, out)
        st.done[pos].add(j)
        stamp[(pos, j)] = -1
        touched = list(st.dirty)
        st.dirty.clear()
        for c, jj in touched:
            for other in on.get(c, ()):
                push(other, jj)
