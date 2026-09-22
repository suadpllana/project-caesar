"""The loop, and the estimate it chooses on.

The unit of work is one chunk of one condition. A pending pair is scored by the rows it is
expected to leave alive: the smaller of the survivors that chunk still holds and the count for
that condition on it, which is the header's interpolation until the chunk has been read and its
exact count afterwards. The smallest score is taken, a tie going to the condition written
earlier and then to the lower chunk. After every pair the scores move, because the pair just
decided changed the survivor counts and may have replaced a header guess with an exact count,
so the choice is made again rather than settled once.
"""
from scn import hdr, live, step


def bound(seg, st, ch, cond):
    got = st.hit.get((ch.c, ch.j, cond.pos))
    return hdr.guess(seg, ch, cond) if got is None else got


def run(seg, q, st, out):
    while True:
        best = None
        for cd in q.conds:
            done = st.done[cd.pos]
            for ch in seg.cols[cd.c]:
                j = ch.j
                if j in done:
                    continue
                have = live.count(st, cd.c, j)
                if have <= 0:
                    continue
                b = bound(seg, st, ch, cd)
                if b > have:
                    b = have
                if best is None or b < best[0]:
                    best = (b, cd, j)
        if best is None:
            return
        cd, j = best[1], best[2]
        step.decide(seg, q, st, cd, j, out)
        st.done[cd.pos].add(j)
