from . import addr, grid, memo


def cone(st, a):
    rows = memo.index(st)
    out = []
    for r in sorted(rows):
        if r > a[0]:
            break
        for o in rows[r]:
            if o[1] <= a[1]:
                out.append(o)
    return out


def rect(st, o):
    if o in st.lays:
        return st.lays[o]
    v = memo.value(st, o)
    out = None
    if grid.is_blk(v):
        h, w = v[1], v[2]
        if o[0] + h <= addr.ROWH + 1 and o[1] + w <= addr.COLW:
            out = (h, w) if free(st, o, h, w) else None
    st.lays[o] = out
    return out


def free(st, o, h, w):
    for dr in range(h):
        for dc in range(w):
            c = (o[0] + dr, o[1] + dc)
            if c == o:
                continue
            if st.sheet.held(c):
                return False
            for p in cone(st, c):
                if not p < o:
                    break
                got = rect(st, p)
                if got and c[0] < p[0] + got[0] and c[1] < p[1] + got[1]:
                    return False
    return True
