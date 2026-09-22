"""The dictionary of a chunk, when it may be used and what it charges.

A dictionary only speaks for its chunk when it covers every row: one literal in the overflow
list and the chunk has to be read. The charge is per chunk, not per consult, so the second
condition to reach a dictionary chunk pays nothing, which makes the printed reads a function of
which consult got there first - a condition in the choice loop or the report pass.

The report pass can take a value from a dictionary too: one entry, no overflow and no nulls
means every row holds that entry, which a header rounded inward cannot show on its own.
"""
from scn import rd


def usable(ch):
    return ch.enc == "d" and not ch.lit


def charge(ch, st, out):
    key = (ch.c, ch.j)
    if key not in st.dread:
        st.dread.add(key)
        out.rd(ch.c, ch.j)


def decide(seg, ch, cond, st, out):
    charge(ch, st, out)
    good = 0
    for v in ch.dic:
        if rd.sat(cond, v):
            good += 1
    if good == 0:
        return "drop"
    if good == len(ch.dic) and ch.nulls == 0:
        return "keep"
    return "read"


def single(ch):
    return usable(ch) and len(ch.dic) == 1 and ch.nulls == 0
