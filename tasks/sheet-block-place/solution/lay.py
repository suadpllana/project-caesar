from . import addr, grid, memo


def cone(st, a):
    return [o for o in st.sheet.owners() if o[0] <= a[0] and o[1] <= a[1]]


def rect(st, o):
    hit = st.lays.get(o)
    if hit is not None:
        return hit[0]
    v = memo.value(st, o)
    out = None
    if grid.is_blk(v):
        h, w = v[1], v[2]
        if o[0] + h - 1 <= addr.ROWH and o[1] + w - 1 < addr.COLW and clear(st, o, h, w):
            out = (h, w)
    st.lays[o] = (out,)
    return out


def clear(st, o, h, w):
    for c in addr.span(o, h, w):
        if c == o:
            continue
        if st.sheet.held(c):
            return False
        if taken(st, c, o):
            return False
    return True


def taken(st, c, o):
    for p in cone(st, c):
        if not p < o:
            break
        got = rect(st, p)
        if got is None:
            continue
        if c[0] < p[0] + got[0] and c[1] < p[1] + got[1]:
            return True
    return False
