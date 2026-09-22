"""Correct variant: the reported figures are accumulated chunk by chunk."""
import bisect

from scn import live, step


def run(seg, q, st, rows, out):
    for c in q.cols:
        cols = seg.cols[c]
        for ch in cols:
            if live.count(st, c, ch.j) > 0 and (c, ch.j) not in st.vals:
                step.load(seg, q, st, ch, out)
        starts = st.starts[c]
        good = 0
        total = 0
        for r in rows:
            j = bisect.bisect_right(starts, r) - 1
            v = st.vals[(c, j)][r - starts[j]]
            if v is not None:
                good += 1
                total += v
        out.prj(c, good, total)
