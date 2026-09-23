"""The loop, and the estimate it chooses on.

The unit of work is one chunk of one condition. A pending pair is scored by the rows it is
expected to leave alive: the smaller of the live rows that chunk still holds and the condition's
count on it, which is the sum over its pages of the exact count where a page has been read and
the header's spread where it has not. The smallest score is taken, a tie going to the condition
written earlier and then to the lower chunk.

Rescanning every pending pair after every step is correct and far too slow once a column has a
thousand chunks, so the scores live in a heap keyed exactly as the order is. A score moves only
when its chunk's live count moves or one of its pages is read, and those chunks are the ones the
step marked dirty; each of their pending pairs is pushed again with its current score. The move
can go either way - deaths lower a score, and a read can replace a low spread with a higher
exact count - so a popped entry is trusted only while it still equals the pair's current score.
"""
import heapq

from scn import live, step


def score(st, cond, j):
    have = live.count(st, cond.c, j)
    b = st.cnt[(cond.pos, j)]
    return have if have < b else b


def run(seg, q, st, out):
    on = {}
    for cd in q.conds:
        on.setdefault(cd.c, []).append(cd)
    heap = []
    for cd in q.conds:
        for ch in seg.cols[cd.c]:
            if live.count(st, cd.c, ch.j) > 0:
                heap.append((score(st, cd, ch.j), cd.pos, ch.j))
    heapq.heapify(heap)
    conds = q.conds
    st.dirty.clear()
    while heap:
        s, pos, j = heapq.heappop(heap)
        cd = conds[pos]
        if j in st.done[pos] or live.count(st, cd.c, j) <= 0:
            continue
        if s != score(st, cd, j):
            continue
        step.decide(seg, q, st, cd, j, out)
        st.done[pos].add(j)
        for c, jj in st.dirty:
            for other in on.get(c, ()):
                if jj in st.done[other.pos] or live.count(st, c, jj) <= 0:
                    continue
                heapq.heappush(heap, (score(st, other, jj), other.pos, jj))
        st.dirty.clear()
