"""The dictionary of a chunk, when it may be used and what it charges.

A dictionary only decides when it covers every row of its chunk: one literal in the overflow
list and the chunk has to be read. The charge is per chunk, not per consult, so the second
condition to reach a dictionary chunk pays nothing, which makes the printed reads a function of
which condition got there first.
"""
from scn import rd


def usable(ch):
    return ch.enc == "d" and not ch.lit


def decide(seg, ch, cond, st, out):
    key = (ch.c, ch.j)
    if key not in st.dread:
        st.dread.add(key)
        out.rd(ch.c, ch.j)
    good = 0
    for v in ch.dic:
        if rd.sat(cond, v):
            good += 1
    if good == 0:
        return "drop"
    if good == len(ch.dic) and ch.nulls == 0:
        return "keep"
    return "read"
