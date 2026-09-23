"""Correct variant: the pending pairs sit in a segment tree of exact minima.

Slots are laid out condition by condition and chunk by chunk, so the smallest (score, slot) is
the order's own tie-break. A score that moves either way is overwritten where it stands, and a
condition's count on a chunk is summed afresh from its pages whenever the chunk is touched.
"""
from scn import hdr, live, step


def run(seg, q, st, out):
    base = []
    at = 0
    for cd in q.conds:
        base.append(at)
        at += len(seg.cols[cd.c])
    size = 1
    while size < max(1, at):
        size *= 2
    tree = [None] * (2 * size)

    def put(i, key):
        i += size
        tree[i] = key
        i >>= 1
        while i:
            a, b = tree[2 * i], tree[2 * i + 1]
            tree[i] = b if a is None else (a if b is None or a <= b else b)
            i >>= 1

    def fresh(cd, j):
        slot = base[cd.pos] + j
        have = live.count(st, cd.c, j)
        if j in st.done[cd.pos] or have <= 0:
            put(slot, None)
            return
        total = 0
        for pg in seg.cols[cd.c][j].pages:
            if (pg.c, pg.j, pg.p) in st.mem.vals:
                total += live.exact(st, cd, pg)
            else:
                total += hdr.guess(seg, pg, cd)
        put(slot, (min(have, total), slot, cd.pos, j))

    on = {}
    for cd in q.conds:
        on.setdefault(cd.c, []).append(cd)
        for ch in seg.cols[cd.c]:
            fresh(cd, ch.j)
    st.dirty.clear()
    while tree[1] is not None:
        _s, _slot, pos, j = tree[1]
        cd = q.conds[pos]
        step.decide(seg, q, st, cd, j, out)
        st.done[pos].add(j)
        st.dirty.add((cd.c, j))
        touched = list(st.dirty)
        st.dirty.clear()
        for c, jj in touched:
            for other in on.get(c, ()):
                fresh(other, jj)
