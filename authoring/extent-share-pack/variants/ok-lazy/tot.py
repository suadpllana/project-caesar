def use(st, vn):
    got = st.row.get(vn)
    return got[0] if got else 0


def held(st):
    return st.held
