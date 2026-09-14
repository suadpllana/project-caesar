def gain(st, vn):
    n = 0
    for e in st.e.values():
        if e.vp == {vn}:
            n += e.siz
    return n
