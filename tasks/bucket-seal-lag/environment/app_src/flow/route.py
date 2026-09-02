def span(g, a):
    d = {}
    work = [(n, lag) for n, lag in g.out[a]]
    while work:
        n, v = work.pop()
        if n in d and d[n] <= v:
            continue
        d[n] = v
        for m, lag in g.out[n]:
            work.append((m, v + lag))
    return d


def carry(st, a, x, b):
    if x is None:
        return None
    d = span(st.g, a)
    if b not in d:
        return None
    y = x + d[b]
    return y if y < st.g.hz else None
