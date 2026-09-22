"""The report pass.

Only chunks that still hold a survivor are read, and only those the condition phase did not
already read, so what this pass prints is a function of the order that phase happened to take.
Columns are worked in the order the query names them.
"""
from scn import live, step


def run(seg, q, st, rows, out):
    for c in q.cols:
        for ch in seg.cols[c]:
            if live.count(st, c, ch.j) > 0 and (c, ch.j) not in st.vals:
                step.load(seg, q, st, ch, out)
        own = st.own[c]
        vals = st.vals
        cols = seg.cols[c]
        nn = 0
        tot = 0
        for r in rows:
            j = own[r]
            v = vals[(c, j)][r - cols[j].start]
            if v is not None:
                nn += 1
                tot += v
        out.prj(c, nn, tot)
