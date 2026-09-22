from scn import rd


def usable(ch):
    return ch.enc == "d"


def decide(seg, ch, cond, st, out):
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
