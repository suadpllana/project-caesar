def reach(b, t):
    c = {}
    for n in b.who():
        k = 0
        for o in b.line(n):
            if o.dt > t:
                break
            k += 1
        c[n] = k
    return c
