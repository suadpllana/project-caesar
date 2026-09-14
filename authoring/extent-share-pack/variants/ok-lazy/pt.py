from st import ext


def put(st, vn, f, i, e, b):
    clr(st, vn, f, i)
    ext.shift(st, e, -1)
    f.s[i] = (e, b)
    e.occ[b] = e.occ.get(b, 0) + 1
    e.vp[vn] = e.vp.get(vn, 0) + 1
    mine = e.vo.get(vn)
    if mine is None:
        mine = e.vo[vn] = {}
    mine[b] = mine.get(b, 0) + 1
    e.ref[(id(f), i)] = f
    ext.shift(st, e, 1)


def clr(st, vn, f, i):
    p = f.s[i]
    if p is None:
        return
    e, b = p
    ext.shift(st, e, -1)
    f.s[i] = None
    if e.occ[b] == 1:
        del e.occ[b]
    else:
        e.occ[b] -= 1
    if e.vp[vn] == 1:
        del e.vp[vn]
    else:
        e.vp[vn] -= 1
    mine = e.vo[vn]
    if mine[b] == 1:
        del mine[b]
        if not mine:
            del e.vo[vn]
    else:
        mine[b] -= 1
    del e.ref[(id(f), i)]
    ext.shift(st, e, 1)
    st.hot.add(e.id)


def wipe(st, v, vn):
    for f in v.f.values():
        for i, p in enumerate(f.s):
            if p is not None:
                clr(st, vn, f, i)
