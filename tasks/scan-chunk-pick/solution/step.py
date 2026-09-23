"""Applying one condition to one chunk, page by page.

By the time a pair is applied, everything that costs nothing has already been done: the header
verdicts, the updated values, the remembered pages and the dictionaries already consulted were
put to every condition when the query started, and every consult and read since has been put to
every condition over its column as it happened. What is left for the pair is the pages still
open for its condition that still supply a live row, in page order. For a comparison on an `i`
page whose dictionary has not been consulted, the dictionary comes first, however little it
turns out to settle, and what it settles it settles for every open `i` page of the chunk and
every comparison over the column. A page still open after that is read.

A read settles every condition of the query over that column on that page, counted over the page
as written, and the file remembers the page.
"""
from scn import dct, live, rd


def load(seg, st, ch, pg, out):
    out.dc(ch.c, ch.j, pg.p)
    vals = rd.values(ch, pg)
    st.mem.vals[(ch.c, ch.j, pg.p)] = vals
    return vals


def decide(seg, q, st, cond, j, out):
    c = cond.c
    ch = seg.cols[c][j]
    opened = st.open[cond.pos]
    for pg in ch.pages:
        key = (j, pg.p)
        if key not in opened or not live.held(st, c, pg):
            continue
        if cond.kind not in ("nn", "nu") and dct.usable(ch, pg) and not dct.known(st, ch):
            dct.charge(ch, st, out)
            live.settle_dict(st, ch)
            if key not in opened or not live.held(st, c, pg):
                continue
        vals = load(seg, st, ch, pg, out)
        live.settle_read(st, ch, pg, vals)
