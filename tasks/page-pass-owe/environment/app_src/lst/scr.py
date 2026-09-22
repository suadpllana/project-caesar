from lst import seq


class Scroll(object):
    def __init__(self, s, g, n, c):
        self.g = g
        self.n = n
        self.c = c
        self.mk = None
        self.led = {}


class State(object):
    def __init__(self, hold):
        self.hold = hold
        self.rows = {}
        self.view = seq.View()
        self.scrolls = {}
        self.got = set()


def open_scroll(st, s, g, n, c):
    st.scrolls[s] = Scroll(s, g, n, c)


def reading(st, g):
    out = []
    for s in sorted(st.scrolls):
        sc = st.scrolls[s]
        if sc.g == g:
            out.append(sc)
    return out


def looked(sc, pl):
    sc.mk = pl


def gave(st, sc, i):
    st.got.add(i)


def had(st, sc, i):
    return i in st.got
