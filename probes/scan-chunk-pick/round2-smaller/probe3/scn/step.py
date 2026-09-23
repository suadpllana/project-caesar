from scn import rd


def load(seg, st, ch, out):
    """Read a chunk (prints `dc`), overlay updates and cache it. Callers
    check st.vals themselves first, so a chunk is only ever loaded once
    per query."""
    out.dc(ch.c, ch.j)
    vals = list(rd.values(ch))
    up = seg.up[ch.c]
    s = ch.start
    for i in range(ch.n):
        r = s + i
        if r in up:
            vals[i] = up[r]
    st.vals[(ch.c, ch.j)] = vals
    return vals
