from . import addr, grid, memo


def cone(st, a):
    return [o for o in st.sheet.owners() if o[0] <= a[0] and o[1] <= a[1]]


def rect(st, o):
    return memo.ask(st, memo.LAY, o, lambda: decide(st, o))


def decide(st, o):
    v = memo.value(st, o)
    if not grid.is_blk(v):
        return None
    h, w = v[1], v[2]
    if o[0] + h - 1 > addr.ROWH or o[1] + w - 1 >= addr.COLW:
        return None
    for c in addr.span(o, h, w):
        if c == o:
            continue
        if st.sheet.held(c) or blocked(st, c, o):
            return None
    return (h, w)


def blocked(st, c, o):
    for p in cone(st, c):
        if p >= o:
            return False
        got = rect(st, p)
        if got is not None and c[0] - p[0] < got[0] and c[1] - p[1] < got[1]:
            return True
    return False
