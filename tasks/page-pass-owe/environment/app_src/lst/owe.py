def held(st):
    total = 0
    for s in st.scrolls:
        for i in st.scrolls[s].led:
            total += st.scrolls[s].led[i]
    return total


def owe(st, sc, i):
    if i in sc.led:
        return
    sc.led[i] = st.rows[i][2]


def unowe(st, sc, i):
    sc.led.pop(i, None)


def settle(st, sc, i):
    r = st.rows.get(i)
    if r is None:
        return
    if r[1] != sc.g:
        return
    if sc.mk is not None and (r[0], i) <= sc.mk:
        if held(st) + r[2] <= st.hold:
            owe(st, sc, i)


def front(sc):
    for i in sc.led:
        return i
    return None


def standing(sc):
    return len(sc.led)
