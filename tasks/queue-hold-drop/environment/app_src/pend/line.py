def about(c):
    return c.a


def names(c):
    if c.kind == "new" and c.b != "-":
        return (c.a, c.b)
    return (c.a,)


def waiting(st):
    return 0 if st.q else -1


def take(st, c):
    st.q.append(c)
