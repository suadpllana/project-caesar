def _bx(st):
    x = st.bx.get("own")
    if x is None:
        x = st.bx["own"] = {"lk": {}, "bl": {}}
    return x


def links(st, a):
    return _bx(st)["lk"].get(a) or {}


def blob(st, t):
    return _bx(st)["bl"].get(t) or {}


def at(st, t):
    m = _bx(st)["bl"].get(t)
    if not m:
        return None
    return m[min(m)]


def keep(st, a, m):
    lk = _bx(st)["lk"]
    if m:
        lk[a] = m
    else:
        lk.pop(a, None)


def hold(st, t, m):
    bl = _bx(st)["bl"]
    if m:
        bl[t] = m
    else:
        bl.pop(t, None)
