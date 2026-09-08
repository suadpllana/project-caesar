from bil import own


def spot(st, d):
    while d is not None:
        up = st.dirs[d].up
        if up is None:
            return st.spn.get(d)
        d = up
    return None


def sweep(st):
    out = {}
    for t in list(st.bx.get("own", {}).get("bl", {})):
        d = own.at(st, t)
        if d is None:
            continue
        nm = spot(st, d)
        if nm is not None:
            out[nm] = out.get(nm, 0) + st.blob.get(t, 0)
    return out


def use(st, nm):
    return sweep(st).get(nm, 0)


def under(st, d):
    n = 0
    seen = set()
    stk = [d]
    while stk:
        x = stk.pop()
        for e in st.dirs[x].ent.values():
            if e[0] == "d":
                stk.append(e[1])
                continue
            t = st.itm[e[1]].tag
            if t not in seen and own.at(st, t) == x:
                seen.add(t)
                n += st.blob.get(t, 0)
    return n


def chain(st, d, n):
    return None


def forget(st, d):
    return None
