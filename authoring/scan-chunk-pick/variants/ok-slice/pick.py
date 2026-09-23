"""Correct variant: a heap whose entries carry a stamp, and a stamp that goes stale is skipped."""
import heapq

from scn import live, step


def run(seg, q, st, out):
    stamp = {}
    heap = []

    def push(cd, j):
        if j in st.done[cd.pos]:
            return
        have = live.count(st, cd.c, j)
        if have <= 0:
            return
        b = live.chunk_count(st, cd, seg.cols[cd.c][j])
        key = (cd.pos, j)
        stamp[key] = stamp.get(key, 0) + 1
        heapq.heappush(heap, (min(have, b), cd.pos, j, stamp[key]))

    for cd in q.conds:
        for ch in seg.cols[cd.c]:
            push(cd, ch.j)
    st.dirty.clear()
    while heap:
        _s, pos, j, mark = heapq.heappop(heap)
        if stamp.get((pos, j)) != mark or j in st.done[pos]:
            continue
        cd = q.conds[pos]
        if not live.pending(st, cd, j):
            st.done[pos].add(j)
            continue
        step.decide(seg, q, st, cd, j, out)
        st.done[pos].add(j)
        stamp[(pos, j)] = -1
        touched = list(st.dirty)
        st.dirty.clear()
        for c, jj in touched:
            for other in st.on.get(c, ()):
                push(other, jj)
