def _bx(st):
    x = st.bx.get("own")
    if x is None:
        x = st.bx["own"] = {"lk": {}, "bl": {}}
    return x


def links(st, a):
    return _bx(st)["lk"].setdefault(a, {})


def blob(st, t):
    return _bx(st)["bl"].setdefault(t, {})


def at(st, t):
    m = _bx(st)["bl"].get(t)
    if not m:
        return None
    return m[min(m)]


def clear(st, a):
    _bx(st)["lk"].pop(a, None)
