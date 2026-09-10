def trim(a, t):
    a.t = t
    ready = a.q
    a.q = []
    a.out.update(ready)
    return ready
