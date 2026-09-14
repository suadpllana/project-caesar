from st import ext, pt, say


def fit(st, e):
    return len(st.von[e.id]) == 1 and 2 * st.occ[e.id] < e.siz


def pack(st, e):
    vn = next(iter(st.von[e.id]))
    at = {}
    for b in range(e.siz):
        if (e.id, b) in st.bc:
            at[b] = len(at)
    moving = [(f, at[b]) for f, b in st.ref[e.id].values()]
    spots = [i for _f, i in st.ref[e.id]]
    n = ext.make(st, len(at))
    for (f, nb), i in zip(moving, spots):
        pt.clr(st, vn, f, i)
        pt.put(st, vn, f, i, n, nb)
    st.hot.discard(n.id)
    ext.kill(st, e)
    say.pack(st, e.id, n.id, n.siz)
