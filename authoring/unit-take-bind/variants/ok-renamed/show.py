from prog.deck import CLASH, at, row
from prog.unit import find


def out_all(tbl, pgm, from_):
    v = find(pgm, from_)
    if v is None:
        return ()
    bag = []
    for x, b in row(tbl, from_).items():
        if b[0] == CLASH or x in v.hides or x in v.shuts:
            continue
        bag.append((x, b))
    return bag


def out_one(tbl, pgm, from_, x):
    v = find(pgm, from_)
    if v is None:
        return None
    b = at(tbl, from_, x)
    if b is None or b[0] == CLASH or x in v.hides:
        return None
    return b
