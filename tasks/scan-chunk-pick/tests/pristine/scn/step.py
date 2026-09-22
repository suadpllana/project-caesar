from scn import dct, hdr, live, rd


def load(seg, q, st, ch, out, cond=None):
    out.dc(ch.c, ch.j)
    vals = list(rd.values(ch))
    up = seg.up[ch.c]
    for i in range(ch.n):
        if ch.start + i in up:
            vals[i] = up[ch.start + i]
    st.vals[(ch.c, ch.j)] = vals
    if cond is not None:
        t = 0
        for v in vals:
            if rd.sat(cond, v):
                t += 1
        st.hit[(ch.c, ch.j, cond.pos)] = t
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
        vals = load(seg, q, st, ch, out, cond)
    live.filter_chunk(st, c, j, cond, vals)
