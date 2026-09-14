from st import ext, pk, say


def done(st):
    if not st.hot:
        return
    hot, st.hot = st.hot, set()
    for eid in sorted(hot):
        e = st.e.get(eid)
        if e is not None and not e.occ:
            ext.kill(st, e)
            say.gone(st, eid)
    for eid in sorted(hot):
        e = st.e.get(eid)
        if e is not None and pk.fit(st, e):
            pk.pack(st, e)
