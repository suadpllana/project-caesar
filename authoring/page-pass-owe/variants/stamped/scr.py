"""Scroll records; the ledger lives here as an append-only order with stamps."""

from lst import seq


class Scroll(object):
    def __init__(self, s, g, n, c):
        self.g = g
        self.n = n
        self.c = c
        self.mk = None
        self.order = []
        self.stamp = {}
        self.live = {}
        self.head = 0
        self.tick = 0
        self.tot = 0
        self.got = set()


class State(object):
    def __init__(self, hold):
        self.hold = hold
        self.rows = {}
        self.view = seq.View()
        self.scrolls = {}
        self.by_tag = {}


def open_scroll(st, s, g, n, c):
    sc = Scroll(s, g, n, c)
    st.scrolls[s] = sc
    st.by_tag.setdefault(g, []).append(sc)


def reading(st, g):
    return st.by_tag.get(g, ())


def looked(sc, pl):
    sc.mk = pl


def gave(sc, i):
    sc.got.add(i)


def had(sc, i):
    return i in sc.got
