from prog.deck import UNIT, at
from prog.unit import find


def cost(rs, rv):
    return (rs if rs > rv else rv) + 1


def srcs(deck, prog, u, s):
    out = []
    b = at(deck, u.nm, s)
    if b is not None and b[0] == UNIT:
        out.append((b[1], b[2]))
    if find(prog, s) is not None:
        out.append((s, 0))
    return out
