"""Correct variant: the dictionary's verdict worked out per call, nothing cached."""
from scn import rd


def usable(ch, pg):
    return ch.enc == "d" and pg.form == "i"


def known(st, ch):
    return (ch.c, ch.j) in st.mem.dread


def charge(ch, st, out):
    if (ch.c, ch.j) not in st.mem.dread:
        st.mem.dread.add((ch.c, ch.j))
        out.rd(ch.c, ch.j)


def verdict(ch, cond):
    hits = [rd.sat(cond, v) for v in ch.dic]
    if not any(hits):
        return "drop"
    if all(hits):
        return "keep"
    return "read"
