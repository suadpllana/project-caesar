from st import ext, pk, say


def done(st):
    hot = st.hot
    st.hot = set()
    for eid in sorted(hot):
        e = st.e.get(eid)
        if e is not None and ext.occ(e) == 0:
            ext.kill(st, e)
            say.gone(st, eid)
    for eid in sorted(hot):
        e = st.e.get(eid)
        if e is not None and pk.fit(st, e):
            pk.pack(st, e)
