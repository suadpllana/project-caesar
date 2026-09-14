"""The settle that follows an op: what is given up, then what is rewritten.

Only the extents noted during the op are looked at. Nothing else can have changed, because losing
a pointer is the only way an extent becomes eligible for either.
"""

from st import ext, pk, say


def done(st):
    hot = st.hot
    if not hot:
        return
    st.hot = set()
    for eid in sorted(hot):
        e = st.e.get(eid)
        if e is not None and e.occ == 0:
            ext.kill(st, e)
            say.gone(st, eid)
    for eid in sorted(hot):
        e = st.e.get(eid)
        if e is not None and pk.fit(st, e):
            pk.pack(st, e)
