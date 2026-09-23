from scn import dct, hdr, live, rd

_CMP = ("ge", "le", "eq", "ne")


def apply(seg, st, cond, ch, out):
    """Apply one (condition, chunk) pending pair: walk its pages in order,
    settling or reading only what is still needed."""
    mem = st.mem
    up = seg.up[cond.c]
    alive = st.alive
    for pg in ch.pages:
        pend = [r for r in range(pg.start, pg.start + pg.n) if alive[r] and r not in up]
        if not pend:
            continue
        if hdr.miss(seg, pg, cond):
            live.kill(st, pend)
            continue
        if hdr.allsat(seg, pg, cond):
            continue
        if pg.form == "i" and cond.kind in _CMP:
            live.ensure_dict(mem, ch, out)
            sat_ct = dct.sat_count(ch, cond)
            if sat_ct == 0:
                live.kill(st, pend)
                continue
            if sat_ct == len(ch.dic) and pg.nulls == 0:
                continue
        vals = live.ensure_page(mem, ch, pg, out)
        dead = [r for r in pend if not rd.sat(cond, vals[r - pg.start])]
        if dead:
            live.kill(st, dead)
