"""Applying one condition to one chunk, page by page, and what a read settles.

A page's header and the chunk's dictionary describe the page as written, and a row with an
update no longer takes its value from it. So each page is decided in two halves: the live rows
carrying an update are tested on their new value, which costs nothing, and only the rest are put
to the header, then to a read already made, then - for a comparison on an `i` page - to the
dictionary, then to a read of that page alone. A page with nothing alive that it still supplies
is not consulted for or read. The dictionary's verdict is worked out once for the pair and then
holds for each of its `i` pages; a verdict that every entry passes still sends a page holding a
null to a read.

A read settles every condition of the query over that column on that page, counted over the page
as written, and the file remembers the page.
"""
from scn import dct, hdr, live, rd


def load(seg, q, st, ch, pg, out):
    out.dc(ch.c, ch.j, pg.p)
    vals = rd.values(ch, pg)
    st.mem.vals[(ch.c, ch.j, pg.p)] = vals
    live.learn(st, q, ch, pg)
    return vals


def decide(seg, q, st, cond, j, out):
    c = cond.c
    ch = seg.cols[c][j]
    up = seg.up[c]
    dead = []
    verdict = None
    for pg in ch.pages:
        held, moved = live.split(st, c, pg)
        dead.extend(r for r in moved if not rd.sat(cond, up[r]))
        if not held:
            continue
        if hdr.miss(seg, pg, cond):
            dead.extend(held)
            continue
        if hdr.allsat(seg, pg, cond):
            continue
        vals = st.mem.vals.get((c, j, pg.p))
        if vals is None and cond.kind not in ("nn", "nu") and dct.usable(ch, pg):
            if verdict is None:
                verdict = dct.decide(seg, ch, cond, st, out)
            if verdict == "drop":
                dead.extend(held)
                continue
            if verdict == "keep" and pg.nulls == 0:
                continue
        if vals is None:
            vals = load(seg, q, st, ch, pg, out)
        s = pg.start
        dead.extend(r for r in held if not rd.sat(cond, vals[r - s]))
    live.kill(st, dead)
