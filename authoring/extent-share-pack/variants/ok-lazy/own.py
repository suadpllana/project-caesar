def gain(st, vn):
    got = st.row.get(vn)
    return got[1] + got[2] if got else 0
