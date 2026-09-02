from flow import emit


def step(st, n, y):
    g = st.g
    k = g.kind[n]
    if k == "relay":
        return y
    if k == "lift":
        return max(y, g.par[n])
    if k == "gather":
        w = g.par[n]
        return (y // w + 1) * w - 1
    return None


def land(st):
    g = st.g
    out, arr = {}, {}
    for n in g.names:
        v = emit.own(st, n)
        if v is not None and v < g.hz:
            out[n] = v
    moving = True
    while moving:
        moving = False
        for u in sorted(out):
            for d, lag in g.out[u]:
                y = out[u] + lag
                if y >= g.hz:
                    continue
                if d not in arr or y < arr[d]:
                    arr[d] = y
                    moving = True
                e = step(st, d, y)
                if e is None or e >= g.hz:
                    continue
                if d not in out or e < out[d]:
                    out[d] = e
                    moving = True
    return arr


def ripe(st, gn, b):
    hi = (b + 1) * st.g.par[gn] - 1
    for x in st.box[gn]:
        if x <= hi:
            return False
    v = land(st).get(gn)
    return v is None or v > hi
