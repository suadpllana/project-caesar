"""Ledger order by list links, weight held as a sum over per-scroll totals."""

from lst import scr


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
    if i in sc.node:
        return
    nd = scr.Node(i, st.rows[i][2])
    if sc.tail is None:
        sc.head = nd
        sc.tail = nd
    else:
        nd.prev = sc.tail
        sc.tail.next = nd
        sc.tail = nd
    sc.node[i] = nd
    sc.tot += nd.w


def unowe(st, sc, i):
    nd = sc.node.pop(i, None)
    if nd is None:
        return
    if nd.prev is None:
        sc.head = nd.next
    else:
        nd.prev.next = nd.next
    if nd.next is None:
        sc.tail = nd.prev
    else:
        nd.next.prev = nd.prev
    sc.tot -= nd.w


def settle(st, sc, i):
    if owed_here(st, sc, i):
        owe(st, sc, i)
    else:
        unowe(st, sc, i)


def front(sc):
    return sc.head.i if sc.head is not None else None


def standing(sc):
    return len(sc.node)


def weight(sc):
    return sc.tot
