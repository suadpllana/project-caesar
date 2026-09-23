"""A chunk's dictionary: which pages it speaks for, what it settles, and what it charges.

The dictionary belongs to the chunk and speaks only for the chunk's `i` pages - a page that fell
back to plain values is outside it. It is charged once per chunk for the whole file: the first
consult prints, and every later one, in this query or any after it, is free. The report pass can
take a value from it too, when it has a single entry and the page holds no null.
"""
from scn import rd


def usable(ch, pg):
    return ch.enc == "d" and pg.form == "i"


def charge(ch, st, out):
    key = (ch.c, ch.j)
    if key not in st.mem.dread:
        st.mem.dread.add(key)
        out.rd(ch.c, ch.j)


def decide(seg, ch, cond, st, out):
    charge(ch, st, out)
    good = 0
    for v in ch.dic:
        if rd.sat(cond, v):
            good += 1
    if good == 0:
        return "drop"
    if good == len(ch.dic):
        return "keep"
    return "read"


def single(ch, pg):
    return usable(ch, pg) and len(ch.dic) == 1 and pg.nulls == 0
