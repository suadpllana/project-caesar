from . import grid, lay, memo


def face(st, a):
    for o in lay.cone(st, a):
        got = lay.rect(st, o)
        if not got:
            continue
        h, w = got
        if a[0] - o[0] < h and a[1] - o[1] < w:
            return memo.value(st, o)[3][(a[0] - o[0]) * w + (a[1] - o[1])]
    if not st.sheet.held(a):
        return grid.EMPTY
    v = memo.value(st, a)
    if grid.is_blk(v):
        return grid.BLK
    if grid.is_set(v):
        return grid.REF
    return v


def gather(st, lo, hi):
    rs = sorted((lo[0], hi[0]))
    cs = sorted((lo[1], hi[1]))
    out = [face(st, (r, c)) for r in range(rs[0], rs[1] + 1) for c in range(cs[0], cs[1] + 1)]
    return grid.bag(rs[1] - rs[0] + 1, cs[1] - cs[0] + 1, out)
