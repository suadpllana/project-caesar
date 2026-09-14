"""Correct variant: occupancy as the set of blocks that are occupied, totals in one row per volume.

Where the reference carries a tally for every block of an extent whether or not anything is on it,
and three separate per-volume dicts, this carries only the blocks that are occupied and gives each
volume a single row of three numbers. Same contract, different shape.
"""
from st import ids


class Ext:
    __slots__ = ("id", "siz", "occ", "vp", "vo", "ref")

    def __init__(self, eid, siz):
        self.id = eid
        self.siz = siz
        self.occ = {}
        self.vp = {}
        self.vo = {}
        self.ref = {}


def boot(st):
    st.hot = set()
    st.held = 0
    st.row = {}


def row(st, vn):
    got = st.row.get(vn)
    if got is None:
        got = st.row[vn] = [0, 0, 0]
    return got


def make(st, siz):
    e = Ext(ids.take(st), siz)
    st.e[e.id] = e
    st.held += siz
    return e


def kill(st, e):
    st.held -= e.siz
    del st.e[e.id]


def shift(st, e, sign):
    on = list(e.vp)
    for v in on:
        row(st, v)[0] += sign * e.siz
    if len(on) == 1:
        row(st, on[0])[1] += sign * e.siz
    elif len(on) == 2:
        for k in (0, 1):
            other = on[1 - k]
            wide = len(e.vo[other])
            if 2 * wide < e.siz:
                row(st, on[k])[2] += sign * (e.siz - wide)
