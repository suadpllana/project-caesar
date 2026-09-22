"""Correct variant: nothing is maintained.

The survivors are one byte per row and a chunk's count of them is summed off the slice when an
estimate asks, so there is no per-chunk count, no row-to-chunk table and no bookkeeping on a
death at all. It fits the limit because the summing is done by the interpreter's own loop over
a byte slice rather than by a walk over a collection of row ids.
"""
from scn import rd


class State:
    __slots__ = ("seg", "alive", "vals", "hit", "dread", "done")


def start(seg, q):
    st = State()
    st.seg = seg
    st.alive = bytearray(b"\x01" * seg.n)
    st.vals = {}
    st.hit = {}
    st.dread = set()
    st.done = [set() for _ in q.conds]
    return st


def count(st, c, j):
    ch = st.seg.cols[c][j]
    return sum(st.alive[ch.start:ch.start + ch.n])


def kill(st, dead):
    alive = st.alive
    for r in dead:
        alive[r] = 0


def drop_chunk(st, c, j):
    ch = st.seg.cols[c][j]
    st.alive[ch.start:ch.start + ch.n] = bytearray(ch.n)


def filter_chunk(st, c, j, cond, vals):
    ch = st.seg.cols[c][j]
    base = ch.start
    alive = st.alive
    for i in range(ch.n):
        if alive[base + i] and not rd.sat(cond, vals[i]):
            alive[base + i] = 0


def rows(st):
    alive = st.alive
    return [r for r in range(len(alive)) if alive[r]]
