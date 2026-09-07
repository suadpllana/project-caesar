from . import addr, grid


def spread(st):
    out = {}
    for o in st.sheet.owners():
        v = st.vals.get(o)
        if not grid.is_blk(v):
            continue
        h, w = v[1], v[2]
        seats = []
        ok = True
        for k, c in enumerate(addr.span(o, h, w)):
            if not addr.inside(c):
                continue
            if c == o:
                seats.append((c, k))
                continue
            if st.sheet.held(c) or c in out:
                ok = False
                break
            seats.append((c, k))
        if not ok:
            continue
        for c, k in seats:
            out[c] = (o, k)
    return out
