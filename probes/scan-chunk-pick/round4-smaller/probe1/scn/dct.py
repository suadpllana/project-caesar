from scn import rd


def sat_count(ch, cond):
    """How many entries of the chunk's dictionary satisfy cond."""
    n = 0
    for v in ch.dic:
        if rd.sat(cond, v):
            n += 1
    return n
