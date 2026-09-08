from bil import own


def tot(st):
    t = st.bx.get("tot")
    if t is None:
        t = st.bx["tot"] = {}
    return t


def spot(st, d):
    while d is not None:
        up = st.dirs[d].up
        if up is None:
            return st.spn.get(d)
        d = up
    return None


def use(st, nm):
    return tot(st).get(nm, 0)


def bump(st, nm, n):
    if nm is None or not n:
        return
    t = tot(st)
    t[nm] = t.get(nm, 0) + n


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
            if t in seen:
                continue
            if own.head(st, t) == x:
                seen.add(t)
                n += st.blob.get(t, 0)
    return n
