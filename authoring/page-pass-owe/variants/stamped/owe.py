"""Ledger order by stamp, weight held as a sum over per-scroll totals."""


def held(st):
    total = 0
    for s in st.scrolls:
        total += st.scrolls[s].tot
    return total


def owed_here(st, sc, i):
    r = st.rows.get(i)
    if r is None or r[1] != sc.g or i in sc.got:
        return False
    return sc.mk is not None and (r[0], i) <= sc.mk


def owe(st, sc, i):
    if i in sc.live:
        return
    w = st.rows[i][2]
    sc.tick += 1
    sc.stamp[i] = sc.tick
    sc.live[i] = w
    sc.tot += w
    sc.order.append((i, sc.tick))


def unowe(st, sc, i):
    w = sc.live.pop(i, None)
    if w is None:
        return
    sc.tot -= w
    sc.stamp.pop(i, None)


def settle(st, sc, i):
    if owed_here(st, sc, i):
        owe(st, sc, i)
    else:
        unowe(st, sc, i)


def front(sc):
    while sc.head < len(sc.order):
        i, t = sc.order[sc.head]
        if sc.stamp.get(i) == t:
            return i
        sc.head += 1
    return None


def standing(sc):
    return len(sc.live)


def weight(sc):
    return sc.tot
