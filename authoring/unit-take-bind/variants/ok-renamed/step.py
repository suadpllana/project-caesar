from prog.deck import UNIT, at
from prog.unit import find


def cost(hop, held):
    return (hop if hop > held else held) + 1


def srcs(tbl, pgm, u, s):
    out = []
    b = at(tbl, u.nm, s)
    if b is not None and b[0] == UNIT:
        out.append((b[1], b[2]))
    if find(pgm, s) is not None:
        out.append((s, 0))
    return out
