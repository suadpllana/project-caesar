def near(st, sb):
    out = {sb: 0}
    front = [sb]
    d = 0
    while front:
        d += 1
        nxt = []
        for g in st.crews():
            if g in out:
                continue
            for m in st.mems(g):
                if m in front:
                    out[g] = d
                    nxt.append(g)
                    break
        front = nxt
    return out
