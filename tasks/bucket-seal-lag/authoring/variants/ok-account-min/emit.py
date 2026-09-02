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
        seen = [(b + 1) * w - 1 for b in st.buk[n]]
        seen += [(x // w + 1) * w - 1 for x in box]
        return min(seen) if seen else None
    return None
