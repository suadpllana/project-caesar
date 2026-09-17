from . import bind, fold, view


def about(c):
    return c.a


def names(c):
    if c.b is None or c.b == "-" or c.kind in ("set", "add", "cut"):
        return (c.a,)
    return (c.a, c.b)


def waiting(st):
    seen = 0
    for c in st.q:
        if c.sent:
            return seen
        seen += 1
    return -1


def take(st, c):
    if c.kind == "cut" and not bind.got(st, c.a):
        born = [i for i, q in enumerate(st.q) if q.kind == "new" and q.a == c.a]
        if born:
            at = born[0]
            st.q.pop(at)
            fold.sweep(st, at, {c.a})
            view.fresh(st)
            return
    st.q.append(c)
    view.push(st, c)
