def count(a, p):
    n = 0
    for b in a.pset.get(p, ()):
        if a.vc[b] == 0 and a.pc[b] == 1:
            n += 1
    return n
