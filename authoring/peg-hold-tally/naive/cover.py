def pegged(a, p, v, t):
    a.t = t
    held = list(a.have.get(v, ()))
    a.pset[p] = held
    for b in held:
        a.pc[b] += 1
