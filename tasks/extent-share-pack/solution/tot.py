"""The size questions, read off totals that were maintained as the pointers moved."""

def use(st, vn):
    return st.use.get(vn, 0)


def held(st):
    return st.held
