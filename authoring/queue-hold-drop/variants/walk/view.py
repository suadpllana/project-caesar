from . import bind, lay, say

STAMP = "_walk_stamp"


def fresh(st):
    setattr(st, STAMP, None)


def push(st, c):
    held = getattr(st, STAMP, None)
    if held is not None:
        lay.one(held, c)


def of(st):
    held = getattr(st, STAMP, None)
    if held is None:
        held = dict((name, r.copy()) for name, r in st.base.items())
        for c in st.q:
            lay.one(held, c)
        setattr(st, STAMP, held)
    return held


def land(st, c):
    if c.kind == "new":
        bind.arrive(st, c.a)
    lay.one(st.base, c)
    fresh(st)


def _row(st, tag, name, r):
    up = "-" if r.up is None else bind.show(st, r.up)
    return say.shelf(tag, bind.show(st, name), up, r.fld)


def ask(st, name):
    seen = of(st)
    if name not in seen:
        st.out.append("none")
        return
    st.out.append(_row(st, "rec", name, seen[name]))


def all(st):
    seen = of(st)
    for name in list(seen):
        st.out.append(_row(st, "row", name, seen[name]))
