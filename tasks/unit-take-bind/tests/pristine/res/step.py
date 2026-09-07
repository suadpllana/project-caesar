from prog.deck import UNIT, at
from prog.unit import find


def cost(rs, rv):
    return rv + 1


def srcs(deck, prog, u, s):
    b = at(deck, u.nm, s)
    if b is not None and b[0] == UNIT:
        return [(b[1], b[2])]
    if find(prog, s) is not None:
        return [(s, 0)]
    return []
