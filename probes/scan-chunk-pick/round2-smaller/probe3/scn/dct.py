from scn import rd


def usable(ch):
    # A dictionary can only settle a comparison when none of its tokens
    # is written with a literal ('*') that bypasses the dictionary.
    return ch.enc == "d" and not ch.lit


def _consult(ch, st, out):
    key = (ch.c, ch.j)
    if key not in st.dread:
        st.dread.add(key)
        out.rd(ch.c, ch.j)


def decide(seg, ch, cond, st, out):
    _consult(ch, st, out)
    good = 0
    for v in ch.dic:
        if rd.sat(cond, v):
            good += 1
    if good == 0:
        return "drop"
    if good == len(ch.dic) and ch.nulls == 0:
        return "keep"
    return "read"


def fixed(seg, ch, st, out):
    """If this usable dictionary chunk holds no nulls and has exactly
    one entry, every row it holds is that entry's value. Consult the
    dictionary (charged, deduped like any other consult) and return
    that value; otherwise return None without consulting it.
    """
    if ch.nulls != 0 or len(ch.dic) != 1:
        return None
    _consult(ch, st, out)
    return ch.dic[0]
