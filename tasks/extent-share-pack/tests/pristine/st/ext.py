from st import ids


class Ext:
    __slots__ = ("id", "siz", "hit", "vp")

    def __init__(self, eid, siz):
        self.id = eid
        self.siz = siz
        self.hit = 0
        self.vp = set()


def boot(st):
    st.hot = set()


def make(st, siz):
    e = Ext(ids.take(st), siz)
    st.e[e.id] = e
    return e


def hold(st, e, blk, d):
    e.hit += d


def occ(e):
    return e.hit


def kill(st, e):
    del st.e[e.id]
