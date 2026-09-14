def gain(st, vn):
    n = 0
    for e in st.e.values():
        if vn not in e.vp:
            continue
        if len(e.vp) == 1:
            n += e.siz
        elif len(e.vp) == 2:
            other = [v for v in e.vp if v != vn][0]
            o = e.vo[other]
            if 2 * o < e.siz:
                n += e.siz - o
    return n
