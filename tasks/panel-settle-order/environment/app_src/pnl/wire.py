def tie(pl, net, g, seen):
    old = net.dep.get(g, set())
    for d in seen - old:
        net.rdr.setdefault(d, set()).add(g)
    net.dep[g] = set(seen)
    return False
