from st import ext


def put(st, vn, f, i, e, b):
    clr(st, vn, f, i)
    f.s[i] = (e, b)
    ext.hold(st, e, b, 1)
    e.vp.add(vn)


def clr(st, vn, f, i):
    p = f.s[i]
    if p is None:
        return
    e, b = p
    f.s[i] = None
    ext.hold(st, e, b, -1)
    e.vp.discard(vn)
    st.hot.add(e.id)


def wipe(st, v, vn):
    for f in v.f.values():
        for i, p in enumerate(f.s):
            if p is None:
                continue
            e, b = p
            f.s[i] = None
            ext.hold(st, e, b, -1)
            e.vp.discard(vn)
