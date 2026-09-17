"""A correct variant: the cap decided before the write, by arithmetic.

What a put leaves the line with is the charge it has, plus what the put adds, less the blocks of
its own that the put stops it holding. The second term is the whole of the difference from the
reference, which lets the write stand and reads the charge instead.
"""
from led import cell, cost, hold, say


def cap(st, name, size):
    cell.line(st, name).cap = size


def leaves(st, name, lo, hi, size):
    one = cell.line(st, name)
    after = cost.charge(st, name) + (hi - lo + 1) * size
    g = hold.kit(st).g
    for c in range(lo, hi + 1):
        chain = one.cells.get(c)
        e = None if chain is None else chain.open()
        if e is None or e.blk.sole != name:
            continue
        keeps = False
        for idx in one.taken:
            if idx < e.born or idx >= g:
                continue
            owner = name
            for i, who in one.away:
                if i == idx:
                    owner = who
            if owner == name:
                keeps = True
                break
        if not keeps:
            after -= e.blk.size
    return after


def put(st, name, lo, hi, size):
    one = cell.line(st, name)
    if one.cap is not None and leaves(st, name, lo, hi, size) > one.cap:
        say.full(st, name)
        return
    made, _shut = cell.write(st, name, lo, hi, size)
    num = st.mint()
    for e in made:
        e.blk.num = num
