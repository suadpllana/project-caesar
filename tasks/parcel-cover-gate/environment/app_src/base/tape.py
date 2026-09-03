class Ver(object):
    __slots__ = ("val", "base", "deps")

    def __init__(self, val, base, deps):
        self.val = val
        self.base = base
        self.deps = deps


class St(object):
    __slots__ = ("vers", "show", "grp", "parc", "bag", "sink", "step")

    def __init__(self, sink):
        self.vers = []
        self.show = {}
        self.grp = {}
        self.parc = []
        self.bag = {}
        self.sink = sink
        self.step = 0


def seat(st, w):
    if w not in st.show:
        st.show[w] = {}
    return st.show[w]


def make(st, w, s, val, base):
    view = seat(st, w)
    st.vers.append(Ver(val, base, dict(view)))
    view[s] = len(st.vers) - 1
    return view[s]


def put(st, w, s, val):
    view = seat(st, w)
    return make(st, w, s, val, (view[s],) if s in view else ())


def mix(st, w, s, no):
    view = seat(st, w)
    if s not in view or no < 1 or no > len(st.parc):
        return -1
    ent = st.parc[no - 1]
    if s not in ent or ent[s] == view[s]:
        return -1
    a, b = view[s], ent[s]
    return make(st, w, s, st.vers[a if a > b else b].val, (a, b))


def read(st, w, s):
    view = seat(st, w)
    if s not in view:
        return "-"
    val = st.vers[view[s]].val
    return "x" if val is None else str(val)
