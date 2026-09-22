"""Correct variant: no survivor counts are maintained.

The survivors are one byte per row and a chunk's count of them is summed off the slice when a
score asks. A death is traced to its chunk in every column by searching that column's chunk
starts, only so the choice loop knows whose scores to look at again.
"""
import bisect

from scn import rd


class State:
    __slots__ = ("seg", "alive", "starts", "vals", "hit", "dread", "done", "dirty", "own")


def start(seg, q):
    st = State()
    st.seg = seg
    st.alive = bytearray(b"\x01" * seg.n)
    for r in seg.gone:
        st.alive[r] = 0
    cols = []
    for cd in q.conds:
        if cd.c not in cols:
            cols.append(cd.c)
    for c in q.cols:
        if c not in cols:
            cols.append(c)
    st.starts = {c: [ch.start for ch in seg.cols[c]] for c in cols}
    st.own = st.starts
    st.vals = {}
    st.hit = {}
    st.dread = set()
    st.done = [set() for _ in q.conds]
    st.dirty = set()
    return st


def count(st, c, j):
    ch = st.seg.cols[c][j]
    return sum(st.alive[ch.start:ch.start + ch.n])


def kill(st, dead):
    alive = st.alive
    for r in dead:
        if alive[r]:
            alive[r] = 0
            for c, starts in st.starts.items():
                st.dirty.add((c, bisect.bisect_right(starts, r) - 1))


def split(st, c, j):
    ch = st.seg.cols[c][j]
    up = st.seg.up[c]
    held = []
    moved = []
    for r in range(ch.start, ch.start + ch.n):
        if st.alive[r]:
            (moved if r in up else held).append(r)
    return held, moved


def rows(st):
    return [r for r, a in enumerate(st.alive) if a]
