"""The report pass.

A reported column needs a chunk only for survivors that still take their value from it; rows
with an update in that column bring their own. Even then the chunk is not read when something
cheaper already fixes every value it holds: a header whose rows are all null, or whose low
equals its high with no nulls, costs nothing, and a dictionary of one entry with no overflow
and no nulls costs its charge. A chunk the condition phase already read is read again by
nobody. Columns are worked in the order the query names them, once per naming.
"""
from scn import dct, hdr, step


def _source(seg, q, st, ch, out):
    vals = st.vals.get((ch.c, ch.j))
    if vals is not None:
        return lambda i: vals[i]
    fixed, v = hdr.pinned(seg, ch)
    if fixed:
        return lambda i: v
    if dct.single(ch):
        dct.charge(ch, st, out)
        one = ch.dic[0]
        return lambda i: one
    vals = step.load(seg, q, st, ch, out)
    return lambda i: vals[i]


def run(seg, q, st, rows, out):
    alive = st.alive
    for c in q.cols:
        up = seg.up[c]
        src = {}
        for ch in seg.cols[c]:
            s = ch.start
            if any(alive[r] and r not in up for r in range(s, s + ch.n)):
                src[ch.j] = _source(seg, q, st, ch, out)
        own = st.own[c]
        cols = seg.cols[c]
        nn = 0
        tot = 0
        for r in rows:
            if r in up:
                v = up[r]
            else:
                j = own[r]
                v = src[j](r - cols[j].start)
            if v is not None:
                nn += 1
                tot += v
        out.prj(c, nn, tot)
