from . import bind, fold, view

TWO = ("new", "mov")


def about(c):
    return c.a


def names(c):
    return (c.a, c.b) if c.kind in TWO and c.b != "-" else (c.a,)


def waiting(st):
    i = 0
    n = len(st.q)
    while i < n:
        if st.q[i].sent:
            return i
        i += 1
    return -1


def take(st, c):
    if c.kind == "cut" and not bind.got(st, c.a):
        for i in range(len(st.q)):
            q = st.q[i]
            if q.kind == "new" and q.a == c.a:
                st.q.pop(i)
                fold.sweep(st, i, {c.a})
                view.fresh(st)
                return
    st.q.append(c)
    view.push(st, c)
