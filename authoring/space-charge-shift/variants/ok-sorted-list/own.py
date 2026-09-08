import bisect


def _bx(st):
    x = st.bx.get("own")
    if x is None:
        x = st.bx["own"] = {"lk": {}, "bl": {}}
    return x


def links(st, a):
    return _bx(st)["lk"].setdefault(a, [])


def blob(st, t):
    return _bx(st)["bl"].setdefault(t, [])


def at(st, t):
    ls = _bx(st)["bl"].get(t)
    return ls[0][1] if ls else None


def clear(st, a):
    _bx(st)["lk"].pop(a, None)


def put(ls, age, d):
    for j in range(len(ls)):
        if ls[j][0] == age:
            ls[j] = (age, d)
            return ls
    bisect.insort(ls, (age, d))
    return ls


def cut(ls, age):
    for j in range(len(ls)):
        if ls[j][0] == age:
            ls.pop(j)
            return ls
    return ls
