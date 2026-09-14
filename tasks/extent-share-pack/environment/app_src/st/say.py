def put(st, eid, siz):
    st.out.append("put %d %d" % (eid, siz))


def gone(st, eid):
    st.out.append("gone %d" % eid)


def pack(st, old, new, siz):
    st.out.append("pack %d %d %d" % (old, new, siz))


def use(st, nm, n):
    st.out.append("use %s %d" % (nm, n))


def own(st, nm, n):
    st.out.append("own %s %d" % (nm, n))


def tot(st, n):
    st.out.append("tot %d" % n)


def at(st, nm, fn, i, e, b):
    if e is None:
        st.out.append("at %s %s %d none" % (nm, fn, i))
    else:
        st.out.append("at %s %s %d %d %d" % (nm, fn, i, e.id, b))
