from scn import rd


def usable(ch):
    return ch.enc == "d"


def known(mem, ch):
    return (ch.c, ch.j) in mem.dicts


def consult(mem, ch, out):
    """Make sure this chunk's dictionary is known, printing rd the first time
    ever (across the whole file) it is consulted."""
    key = (ch.c, ch.j)
    if key not in mem.dicts:
        mem.dicts.add(key)
        out.rd(ch.c, ch.j)


def verdict(ch, pg, cond):
    """Assumes the dictionary is already known. 'miss' / 'allsat' / None (not
    settled) for this specific page, following paragraph 9: no entry
    satisfying it fails every row; every entry satisfying it, with the page
    holding no null, passes every row."""
    good = 0
    for v in ch.dic:
        if rd.sat(cond, v):
            good += 1
    if good == 0:
        return "miss"
    if good == len(ch.dic) and pg.nulls == 0:
        return "allsat"
    return None
