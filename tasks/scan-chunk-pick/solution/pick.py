"""The loop, and the estimate it chooses on.

The unit of work is one chunk of one condition. A pending pair is scored by the rows it is
expected to leave alive: the smaller of the survivors that chunk still holds and the count for
that condition on it, which is the header's interpolation until the chunk has been read and its
exact count afterwards. The smallest score is taken, a tie going to the condition written
earlier and then to the lower chunk.

Rescanning every pending pair after every step is correct and far too slow once a column has a
thousand chunks, so the scores live in a heap keyed exactly as the order is. A score moves only
when its chunk's survivor count moves or its chunk is read, and those chunks are the ones the
step marked dirty; each of their pending pairs is pushed again with its current score. The
move can go either way - deaths lower a score, and a read can replace a low interpolation with
a higher exact count - so a popped entry is trusted only when it still equals the pair's
current score, and a stale one is dropped because a current one was pushed beside it.
"""
import heapq

from scn import hdr, live, step


def bound(seg, st, ch, cond):
    got = st.hit.get((ch.c, ch.j, cond.pos))
    return hdr.guess(seg, ch, cond) if got is None else got


def score(seg, st, cond, j):
    ch = seg.cols[cond.c][j]
    have = live.count(st, cond.c, j)
    b = bound(seg, st, ch, cond)
    return have if have < b else b


def run(seg, q, st, out):
    on = {}
    for cd in q.conds:
        on.setdefault(cd.c, []).append(cd)
    heap = []
    for cd in q.conds:
        for ch in seg.cols[cd.c]:
            if live.count(st, cd.c, ch.j) > 0:
                heap.append((score(seg, st, cd, ch.j), cd.pos, ch.j))
    heapq.heapify(heap)
    conds = q.conds
    st.dirty.clear()
    while heap:
        s, pos, j = heapq.heappop(heap)
        cd = conds[pos]
        if j in st.done[pos] or live.count(st, cd.c, j) <= 0:
            continue
        if s != score(seg, st, cd, j):
            continue
        step.decide(seg, q, st, cd, j, out)
        st.done[pos].add(j)
        for c, jj in st.dirty:
            for other in on.get(c, ()):
                if jj in st.done[other.pos] or live.count(st, c, jj) <= 0:
                    continue
                heapq.heappush(heap, (score(seg, st, other, jj), other.pos, jj))
        st.dirty.clear()
