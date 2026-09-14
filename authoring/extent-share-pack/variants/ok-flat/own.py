def gain(st, vn):
    return st.solo.get(vn, 0) + st.pair.get(vn, 0)
