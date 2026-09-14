from st import ids


class Ext:
    __slots__ = ("id", "siz", "blk", "occ", "vp", "vb", "vo", "ref")

    def __init__(self, eid, siz):
        self.id = eid
        self.siz = siz
        self.blk = [0] * siz
        self.occ = 0
        self.vp = {}
        self.vb = {}
        self.vo = {}
        self.ref = set()


def boot(st):
    st.hot = set()
    st.held = 0
    st.use = {}
    st.solo = {}
    st.pair = {}


def make(st, siz):
    e = Ext(ids.take(st), siz)
    st.e[e.id] = e
    st.held += siz
    return e


def kill(st, e):
    st.held -= e.siz
    del st.e[e.id]


def back(e, v):
    """Blocks the store would give back if v were the last volume left on e."""
    o = e.vo[v]
    return e.siz - o if 2 * o < e.siz else 0


def off(st, e):
    """Take e out of every per-volume total, before its pointers change."""
    for v in e.vp:
        st.use[v] -= e.siz
    if len(e.vp) == 1:
        for v in e.vp:
            st.solo[v] -= e.siz
    elif len(e.vp) == 2:
        a, b = tuple(e.vp)
        st.pair[a] -= back(e, b)
        st.pair[b] -= back(e, a)


def on(st, e):
    """Put e back into every per-volume total, after its pointers changed."""
    for v in e.vp:
        st.use[v] = st.use.get(v, 0) + e.siz
    if len(e.vp) == 1:
        for v in e.vp:
            st.solo[v] = st.solo.get(v, 0) + e.siz
    elif len(e.vp) == 2:
        a, b = tuple(e.vp)
        st.pair[a] = st.pair.get(a, 0) + back(e, b)
        st.pair[b] = st.pair.get(b, 0) + back(e, a)
