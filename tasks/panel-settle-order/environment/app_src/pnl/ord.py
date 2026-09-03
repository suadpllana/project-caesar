def start(net):
    return {"q": [], "in": set(), "tr": set()}


def wake(pl, net, g):
    if g in pl["in"]:
        return
    pl["in"].add(g)
    pl["q"].append(g)


def take(pl, net):
    q = pl["q"]
    if not q:
        return None
    g = q.pop(0)
    pl["in"].discard(g)
    return g
