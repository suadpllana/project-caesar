from flow import emit, route


def ripe(st, gn, b):
    hi = (b + 1) * st.g.par[gn] - 1
    for x in st.box[gn]:
        if x <= hi:
            return False
    for n in st.g.names:
        o = emit.own(st, n)
        if o is None:
            continue
        v = route.carry(st, n, o, gn)
        if v is not None and v <= hi:
            return False
    return True
