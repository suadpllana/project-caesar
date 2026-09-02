BLOC = "+"


def hands(st, cid, on):
    rows = [(st.voter(who), w) for who, w in st.stakes(cid)]
    lump = sum(w for v, w in rows if v in on)
    out = {}
    if lump:
        out[BLOC] = lump
    for v, w in rows:
        if v not in on:
            out[v] = out.get(v, 0) + w
    return out
