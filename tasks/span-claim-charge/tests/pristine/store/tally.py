def setup(st):
    st.ref = {}
    st.excl = {}
    st.own = {}


def start(st, name):
    st.ref[name] = 0
    st.excl[name] = 0
    st.own[name] = set()


def end(st, name):
    del st.ref[name]
    del st.excl[name]
    del st.own[name]


def gain(st, name, sp):
    st.own[name].add(sp)


def lose(st, name, sp):
    st.own[name].discard(sp)


def charge(st, name):
    if name not in st.own:
        return "nosuch"
    ref = 0
    excl = 0
    for sp in st.own[name]:
        for cl in sp.on:
            if cl.own.line == name:
                ref += cl.wide
        if len(sp.on) == 1:
            excl += sp.wide
    return (ref, excl)


def gone(st, names):
    rel = 0
    for name in names:
        if name not in st.own:
            return "nosuch"
        rel += charge(st, name)[1]
    return (rel,)
