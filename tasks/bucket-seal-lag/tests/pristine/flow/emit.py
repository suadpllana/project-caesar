def own(st, n):
    g = st.g
    k = g.kind[n]
    if k == "src":
        return None if st.shut[n] else st.low[n]
    if k == "sink":
        return None
    box = st.box[n]
    if not box:
        return None
    x = min(box)
    if k == "lift" and x < g.par[n]:
        x = g.par[n]
    return x if x < g.hz else None
