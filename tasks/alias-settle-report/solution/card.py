def auth(bk, c):
    best = None
    for (n, k) in bk.post:
        if bk.find(k) == c and (best is None or (n, k) < best):
            best = (n, k)
    return best


def card(bk, c):
    a = auth(bk, c)
    return bk.held(c)[0], (bk.post[a] if a is not None else -1)
