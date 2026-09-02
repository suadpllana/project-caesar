def own(st, n):
    g = st.g
    k = g.kind[n]
    if k == "src":
        return None if st.shut[n] else st.low[n]
    if k == "sink":
        return None
    box = st.box[n]
    if k == "relay":
        return min(box) if box else None
    if k == "lift":
        if not box:
            return None
        x = min(box)
        return x if x >= g.par[n] else g.par[n]
    if k == "gather":
        w = g.par[n]
        best = None
        for b in st.buk[n]:
            v = (b + 1) * w - 1
            if best is None or v < best:
                best = v
        for x in box:
            v = (x // w + 1) * w - 1
            if best is None or v < best:
                best = v
        return best
    return None
