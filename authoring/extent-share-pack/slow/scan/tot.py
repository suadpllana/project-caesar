def use(st, vn):
    n = 0
    for e in st.e.values():
        if vn in e.vp:
            n += e.siz
    return n


def held(st):
    n = 0
    for e in st.e.values():
        n += e.siz
    return n
