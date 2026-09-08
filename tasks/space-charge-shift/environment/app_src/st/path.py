def cut(p):
    return [x for x in p.split("/") if x]


def dirof(st, ps):
    if not ps:
        return None
    d = st.roots.get(ps[0])
    if d is None:
        return None
    for nm in ps[1:]:
        e = st.dirs[d].ent.get(nm)
        if e is None or e[0] != "d":
            return None
        d = e[1]
    return d


def par(st, ps):
    if len(ps) < 2:
        return None
    d = dirof(st, ps[:-1])
    if d is None:
        return None
    return d, ps[-1]


def below(st, d, top):
    while d is not None:
        if d == top:
            return True
        d = st.dirs[d].up
    return False
