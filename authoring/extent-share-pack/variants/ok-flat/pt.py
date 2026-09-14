from st import ext


def put(st, vn, f, i, e, b):
    clr(st, vn, f, i)
    ext.shift(st, e, -1)
    f.s[i] = (e, b)
    key = (e.id, b)
    st.bc[key] = st.bc.get(key, 0) + 1
    if st.bc[key] == 1:
        st.occ[e.id] += 1
    vk = (e.id, vn)
    st.vc[vk] = st.vc.get(vk, 0) + 1
    bk = (e.id, vn, b)
    st.vb[bk] = st.vb.get(bk, 0) + 1
    if st.vb[bk] == 1:
        st.vo[vk] = st.vo.get(vk, 0) + 1
    st.von[e.id].add(vn)
    st.ref[e.id][(id(f), i)] = (f, b)
    ext.shift(st, e, 1)


def clr(st, vn, f, i):
    p = f.s[i]
    if p is None:
        return
    e, b = p
    ext.shift(st, e, -1)
    f.s[i] = None
    key = (e.id, b)
    st.bc[key] -= 1
    if st.bc[key] == 0:
        del st.bc[key]
        st.occ[e.id] -= 1
    vk = (e.id, vn)
    st.vc[vk] -= 1
    if st.vc[vk] == 0:
        del st.vc[vk]
        st.von[e.id].discard(vn)
    bk = (e.id, vn, b)
    st.vb[bk] -= 1
    if st.vb[bk] == 0:
        del st.vb[bk]
        st.vo[vk] -= 1
        if st.vo[vk] == 0:
            del st.vo[vk]
    del st.ref[e.id][(id(f), i)]
    ext.shift(st, e, 1)
    st.hot.add(e.id)


def wipe(st, v, vn):
    for f in v.f.values():
        for i in range(len(f.s)):
            if f.s[i] is not None:
                clr(st, vn, f, i)
