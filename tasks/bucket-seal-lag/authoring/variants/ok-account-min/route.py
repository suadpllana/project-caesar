def step(st, n, y):
    g = st.g
    k = g.kind[n]
    if k == "relay":
        return y
    if k == "lift":
        return y if y >= g.par[n] else g.par[n]
    if k == "gather":
        w = g.par[n]
        return (y // w + 1) * w - 1
    return None


def carry(st, a, x, b):
    g = st.g
    if x is None or x >= g.hz:
        return None
    src = {a: x}
    arr = {}
    live = True
    while live:
        live = False
        for u in sorted(src):
            v = src[u]
            for d, lag in g.out[u]:
                y = v + lag
                if y >= g.hz:
                    continue
                if d not in arr or y < arr[d]:
                    arr[d] = y
                    live = True
                e = step(st, d, y)
                if e is None or e >= g.hz:
                    continue
                if d not in src or e < src[d]:
                    src[d] = e
                    live = True
    return arr.get(b)
