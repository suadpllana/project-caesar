def trim(a, t):
    a.t = t
    ready = [b for b in a.roll if b in a.stop and b not in a.out]
    ready.sort()
    a.out.update(ready)
    return ready
