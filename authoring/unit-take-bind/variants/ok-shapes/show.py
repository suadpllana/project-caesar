from prog.deck import CLASH, at, row
from prog.unit import find


def out_all(deck, prog, vn):
    v = find(prog, vn)
    if v is None:
        return {}
    keep = {}
    for x, b in reversed(list(row(deck, vn).items())):
        if b[0] != CLASH and x not in v.hides and x not in v.shuts:
            keep[x] = b
    return keep


def out_one(deck, prog, vn, x):
    v = find(prog, vn)
    if v is None:
        return None
    b = at(deck, vn, x)
    if b is None or b[0] == CLASH or x in v.hides:
        return None
    return b
