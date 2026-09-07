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




def face(st, a):
    for o in cone(st, a):
        got = rect(st, o)
        if got is None:
            continue
        h, w = got
        if a[0] < o[0] + h and a[1] < o[1] + w:
            v = memo.value(st, o)
            return v[3][(a[0] - o[0]) * w + (a[1] - o[1])]
    if not st.sheet.held(a):
        return grid.EMPTY
    v = memo.value(st, a)
    if grid.is_blk(v):
        return grid.BLK
    if grid.is_set(v):
        return grid.REF
    return v


def gather(st, lo, hi):
    r0, r1 = min(lo[0], hi[0]), max(lo[0], hi[0])
    c0, c1 = min(lo[1], hi[1]), max(lo[1], hi[1])
    out = []
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out.append(face(st, (r, c)))
    return grid.bag(r1 - r0 + 1, c1 - c0 + 1, out)
