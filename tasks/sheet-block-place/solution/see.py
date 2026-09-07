from . import grid, lay, memo


def face(st, a):
    for o in lay.cone(st, a):
        got = lay.rect(st, o)
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
