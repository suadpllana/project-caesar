from . import bind, lay, say


def of(st):
    vw = {}
    for name, r in st.base.items():
        vw[name] = r.copy()
    for c in st.q:
        if c.sent:
            continue
        lay.one(vw, c)
    return vw


def land(st, c):
    if c.kind == "new":
        bind.arrive(st, c.a)
    lay.one(st.base, c)


def ask(st, name):
    r = of(st).get(name)
    if r is None:
        st.out.append("none")
        return
    up = "-" if r.up is None else bind.show(st, r.up)
    st.out.append(say.shelf("rec", bind.show(st, name), up, r.fld))


def all(st):
    for name, r in of(st).items():
        up = "-" if r.up is None else bind.show(st, r.up)
        st.out.append(say.shelf("row", bind.show(st, name), up, r.fld))
