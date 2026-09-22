"""Scroll records: the mark, the delivery memory, and the state they hang off.

Two decisions live here.

The mark is the place of the last row the *scan* looked at, whatever the scan then did
with it - handed it out, passed it by because this scroll already had it, or stepped over
it.  Draining the ledger never moves the mark, because every owed row sits at or before
it already.  A scroll opens with its mark before every place, which is what `None` means:
`View.start` treats it as "begin at the front".

The delivery memory is per scroll and permanent.  A row handed to one scroll says nothing
about another, and a row that leaves a scroll's view and comes back is still one that
scroll has been handed.

`by_tag` is an index from a tag to the scrolls reading it.  An edit touches one row, and
only the scrolls reading that row's old or new tag can care, so the index is what keeps
an edit off the scrolls it cannot reach.
"""

from lst import seq


class Scroll(object):
    def __init__(self, s, g, n, c):
        self.g = g
        self.n = n
        self.c = c
        self.mk = None
        self.led = {}
        self.got = set()


class State(object):
    def __init__(self, hold):
        self.hold = hold
        self.rows = {}
        self.view = seq.View()
        self.scrolls = {}
        self.by_tag = {}
        self.owed = 0


def open_scroll(st, s, g, n, c):
    sc = Scroll(s, g, n, c)
    st.scrolls[s] = sc
    st.by_tag.setdefault(g, []).append(sc)


def reading(st, g):
    out = []
    for s in sorted(st.scrolls):
        if st.scrolls[s].g == g:
            out.append(st.scrolls[s])
    return out


def looked(sc, pl):
    sc.mk = pl


def gave(sc, i):
    sc.got.add(i)


def had(sc, i):
    return i in sc.got
