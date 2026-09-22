from lst import owe
from lst import scr


def add(st, i, k, g, w):
    st.rows[i] = (k, g, w)
    st.view.put(k, i, g)
    for sc in scr.reading(st, g):
        owe.settle(st, sc, i)


def move(st, i, k):
    r = st.rows.get(i)
    if r is None:
        return
    st.view.take(r[0], i, r[1])
    st.rows[i] = (k, r[1], r[2])
    st.view.put(k, i, r[1])


def retag(st, i, g):
    r = st.rows.get(i)
    if r is None:
        return
    st.view.take(r[0], i, r[1])
    st.rows[i] = (r[0], g, r[2])
    st.view.put(r[0], i, g)


def drop(st, i):
    r = st.rows.pop(i, None)
    if r is None:
        return
    st.view.take(r[0], i, r[1])
