"""Deciding one chunk for one condition, and what a decode settles.

The header is asked first, both ways round, then the dictionary where there is a usable one,
and only then is the chunk read. A read settles every condition of the query over that column,
not just the one that asked for it: from then on those conditions are estimated on this chunk
by an exact count rather than by the header, and an engine that records only the asking
condition estimates the rest too high and picks a different chunk to read next.
"""
from scn import dct, hdr, live, rd


def load(seg, q, st, ch, out):
    out.dc(ch.c, ch.j)
    vals = rd.values(ch)
    st.vals[(ch.c, ch.j)] = vals
    for cd in q.conds:
        if cd.c == ch.c:
            t = 0
            for v in vals:
                if rd.sat(cd, v):
                    t += 1
            st.hit[(ch.c, ch.j, cd.pos)] = t
    return vals


def decide(seg, q, st, cond, j, out):
    c = cond.c
    ch = seg.cols[c][j]
    if hdr.miss(seg, ch, cond):
        live.drop_chunk(st, c, j)
        return
    if hdr.allsat(seg, ch, cond):
        return
    vals = st.vals.get((c, j))
    if vals is None:
        if cond.kind not in ("nn", "nu") and dct.usable(ch):
            verdict = dct.decide(seg, ch, cond, st, out)
            if verdict == "drop":
                live.drop_chunk(st, c, j)
                return
            if verdict == "keep":
                return
        vals = load(seg, q, st, ch, out)
    live.filter_chunk(st, c, j, cond, vals)
