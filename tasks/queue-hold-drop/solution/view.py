from . import bind, lay, say


def of(st):
    vw = getattr(st, "vw", None)
    if vw is None:
        vw = {}
        for name, r in st.base.items():
            vw[name] = r.copy()
        for c in st.q:
            lay.one(vw, c)
        st.vw = vw
    return vw


def push(st, c):
    vw = getattr(st, "vw", None)
    if vw is not None:
        lay.one(vw, c)


def fresh(st):
    st.vw = None


def land(st, c):
    if c.kind == "new":
        bind.arrive(st, c.a)
    lay.one(st.base, c)
    fresh(st)


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
