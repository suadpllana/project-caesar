REACH = {}


def _over(st, i):
    got = REACH.get((id(st), i))
    if got is None:
        got = set([i])
        for j in st.vers[i].base:
            got |= _over(st, j)
        REACH[(id(st), i)] = got
    return got


def runs(st, a, b):
    return b in _over(st, a)
