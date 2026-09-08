def ag(st):
    x = st.bx.get("ag")
    if x is None:
        x = st.bx["ag"] = {}
    return x


def spot(st, d):
    while d is not None:
        up = st.dirs[d].up
        if up is None:
            return st.spn.get(d)
        d = up
    return None


def use(st, nm):
    from bil import edit
    edit.watch(st)
    edit.rebuild(st)
    return ag(st).get(st.roots.get(nm), 0)


def under(st, d):
    return ag(st).get(d, 0)


def chain(st, d, n):
    if not n:
        return
    x = ag(st)
    while d is not None:
        x[d] = x.get(d, 0) + n
        d = st.dirs[d].up


def forget(st, d):
    ag(st).pop(d, None)
