def _st(st):
    x = st.bx.get("agg")
    if x is None:
        x = st.bx["agg"] = {"sub": {}, "tot": {}}
    return x


def spot(st, d):
    while d is not None:
        up = st.dirs[d].up
        if up is None:
            return st.spn.get(d)
        d = up
    return None


def use(st, nm):
    return _st(st)["tot"].get(nm, 0)


def under(st, d):
    return _st(st)["sub"].get(d, 0)


def chain(st, d, n):
    if not n:
        return
    x = _st(st)
    top = d
    while d is not None:
        x["sub"][d] = x["sub"].get(d, 0) + n
        top = d
        d = st.dirs[d].up
    nm = st.spn.get(top)
    if nm is not None:
        x["tot"][nm] = x["tot"].get(nm, 0) + n


def forget(st, d):
    _st(st)["sub"].pop(d, None)
