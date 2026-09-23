from scn import rd


def usable(ch):
    # A dictionary can only settle a comparison when every token is either a
    # dictionary index or null -- a chunk holding any literal ('*') token
    # cannot be trusted this way, since that value isn't in the dictionary.
    return ch.enc == "d" and not ch.lit


def mark_consult(st, ch, out):
    """Charge (and print) a dictionary consult, once per query per chunk."""
    key = (ch.c, ch.j)
    if key not in st.dread:
        st.dread.add(key)
        out.rd(ch.c, ch.j)


def decide(seg, ch, cond, st, out):
    mark_consult(st, ch, out)
    good = 0
    for v in ch.dic:
        if rd.sat(cond, v):
            good += 1
    if good == 0:
        return "drop"
    if good == len(ch.dic) and ch.nulls == 0:
        return "keep"
    return "read"
