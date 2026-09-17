from . import bind, fold, view


def about(c):
    return c.a


def names(c):
    if c.kind in ("new", "mov") and c.b != "-":
        return (c.a, c.b)
    return (c.a,)


def waiting(st):
    for i, c in enumerate(st.q):
        if c.sent:
            return i
    return -1


def take(st, c):
    if c.kind == "cut" and not bind.got(st, c.a):
        at = -1
        for i, q in enumerate(st.q):
            if q.kind == "new" and q.a == c.a:
                at = i
                break
        if at >= 0:
            seed = {about(st.q[at])}
            del st.q[at]
            fold.sweep(st, at, seed)
            view.fresh(st)
            return
    st.q.append(c)
    view.push(st, c)
