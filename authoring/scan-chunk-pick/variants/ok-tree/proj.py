"""The report pass.

A reported column needs a page only for the live rows that take their value from it; rows with
an update in that column bring their own. What the line needs from those rows is how many hold a
non-null value and what those values sum to, and that is paid for only when nothing cheaper
answers it: a page already read, or its header when every row is null, when it holds no null and
its bounds are one value, or when those rows are every row the page holds as written - then its
non-null count and its sum are the answer. After those the chunk's dictionary, for an `i` page
with no null when the dictionary has a single entry, for its charge; and a read otherwise.
Columns are worked in the order the query names them, once per naming, pages in order.
"""
from scn import dct, hdr, live, step


def _page(seg, q, st, ch, pg, held, out):
    vals = st.mem.vals.get((ch.c, ch.j, pg.p))
    if vals is None:
        fixed, v = hdr.pinned(seg, pg)
        if fixed:
            return (0, 0) if v is None else (len(held), v * len(held))
        if len(held) == pg.n:
            return pg.n - pg.nulls, pg.sum
        if dct.single(ch, pg):
            dct.charge(ch, st, out)
            return len(held), ch.dic[0] * len(held)
        vals = step.load(seg, q, st, ch, pg, out)
    s = pg.start
    nn = 0
    tot = 0
    for r in held:
        v = vals[r - s]
        if v is not None:
            nn += 1
            tot += v
    return nn, tot


def run(seg, q, st, rows, out):
    for c in q.cols:
        up = seg.up[c]
        nn = 0
        tot = 0
        for ch in seg.cols[c]:
            for pg in ch.pages:
                held, moved = live.split(st, c, pg)
                for r in moved:
                    v = up[r]
                    if v is not None:
                        nn += 1
                        tot += v
                if held:
                    a, b = _page(seg, q, st, ch, pg, held, out)
                    nn += a
                    tot += b
        out.prj(c, nn, tot)
