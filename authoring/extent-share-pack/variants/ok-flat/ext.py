"""Correct variant: nothing hangs off the extent record; the store holds flat tables.

The reference keeps a per-block list, a per-volume dict and a referrer set on each extent object.
This keeps an extent as little more than an id and a size, and puts every tally in a dict on the
store keyed by a tuple. It settles the same contract.
"""
from st import ids


class Ext:
    __slots__ = ("id", "siz")

    def __init__(self, eid, siz):
        self.id = eid
        self.siz = siz


def boot(st):
    st.hot = set()
    st.held = 0
    st.use = {}
    st.solo = {}
    st.pair = {}
    st.bc = {}
    st.vc = {}
    st.vb = {}
    st.occ = {}
    st.vo = {}
    st.von = {}
    st.ref = {}


def make(st, siz):
    e = Ext(ids.take(st), siz)
    st.e[e.id] = e
    st.occ[e.id] = 0
    st.von[e.id] = set()
    st.ref[e.id] = {}
    st.held += siz
    return e


def kill(st, e):
    st.held -= e.siz
    for table in (st.occ, st.von, st.ref):
        del table[e.id]
    del st.e[e.id]


def parts(st, e):
    """(volume, table, amount) for what this extent contributes right now."""
    on = st.von[e.id]
    out = [(v, st.use, e.siz) for v in on]
    if len(on) == 1:
        out.append((next(iter(on)), st.solo, e.siz))
    elif len(on) == 2:
        a, b = tuple(on)
        for me, other in ((a, b), (b, a)):
            o = st.vo[(e.id, other)]
            out.append((me, st.pair, e.siz - o if 2 * o < e.siz else 0))
    return out


def shift(st, e, sign):
    for v, table, amount in parts(st, e):
        table[v] = table.get(v, 0) + sign * amount
