def near(st, sb):
    out = {sb: 0}
    stack = [(sb, 0)]
    while stack:
        who, d = stack.pop()
        for g in st.crews():
            if who not in st.mems(g):
                continue
            if g in out and out[g] <= d + 1:
                continue
            out[g] = d + 1
            stack.append((g, d + 1))
    return out
