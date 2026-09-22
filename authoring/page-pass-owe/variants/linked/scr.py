"""Scroll records; the ledger is a doubly linked list of nodes with a row-to-node map."""

from lst import seq


class Node(object):
    __slots__ = ("i", "w", "prev", "next")

    def __init__(self, i, w):
        self.i = i
        self.w = w
        self.prev = None
        self.next = None


class Scroll(object):
    def __init__(self, s, g, n, c):
        self.g = g
        self.n = n
        self.c = c
        self.mk = None
        self.head = None
        self.tail = None
        self.node = {}
        self.tot = 0
        self.got = {}


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
    sc.got[i] = True


def had(sc, i):
    return i in sc.got
