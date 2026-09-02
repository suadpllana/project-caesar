from flow import emit, route


def ripe(st, gn, b):
    hi = (b + 1) * st.g.par[gn] - 1
    for x in st.box[gn]:
        if x <= hi:
            return False
    for a, lag in st.g.inn[gn]:
        o = emit.own(st, a)
        if o is None:
            continue
        v = route.carry(st, a, o, gn)
        if v is not None and v <= hi:
            return False
    return True
