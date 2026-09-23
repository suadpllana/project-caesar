"""Correct variant: one condition applied to one chunk, page by page."""
from scn import dct, live, rd


def load(seg, st, ch, pg, out):
    out.dc(ch.c, ch.j, pg.p)
    vals = rd.values(ch, pg)
    st.mem.vals[(ch.c, ch.j, pg.p)] = vals
    return vals


def decide(seg, q, st, cond, j, out):
    ch = seg.cols[cond.c][j]
    for pg in ch.pages:
        if not live.open_rows(st, cond, pg):
            continue
        if cond.kind not in ("nn", "nu") and dct.usable(ch, pg) and not dct.known(st, ch):
            dct.charge(ch, st, out)
            live.learned_dict(st, ch)
            if not live.open_rows(st, cond, pg):
                continue
        load(seg, st, ch, pg, out)
        live.learned_page(st, ch, pg)
