"""Correct variant: counts kept in a dict, the owning chunk found by binary search.

There is no row-to-chunk table. A death is charged to one chunk of every column the query
touches by searching that column's chunk starts, and the counts live in one dict keyed by
column and chunk rather than in a list per column.
"""
import bisect

from scn import rd


class State:
    __slots__ = ("seg", "alive", "sv", "starts", "vals", "hit", "dread", "done")


def start(seg, q):
    st = State()
    st.seg = seg
    st.alive = bytearray(b"\x01" * seg.n)
    st.sv = {}
    st.starts = {}
    st.vals = {}
    st.hit = {}
    st.dread = set()
    st.done = [set() for _ in q.conds]
    touched = []
    for cd in q.conds:
        touched.append(cd.c)
    touched.extend(q.cols)
    for c in dict.fromkeys(touched):
        st.starts[c] = [ch.start for ch in seg.cols[c]]
        for ch in seg.cols[c]:
            st.sv[(c, ch.j)] = ch.n
    return st


def count(st, c, j):
    return st.sv[(c, j)]


def kill(st, dead):
    alive = st.alive
    sv = st.sv
    for r in dead:
        if not alive[r]:
            continue
        alive[r] = 0
        for c, starts in st.starts.items():
            sv[(c, bisect.bisect_right(starts, r) - 1)] -= 1


def drop_chunk(st, c, j):
    ch = st.seg.cols[c][j]
    kill(st, range(ch.start, ch.start + ch.n))


def filter_chunk(st, c, j, cond, vals):
    ch = st.seg.cols[c][j]
    base = ch.start
    alive = st.alive
    kill(st, [base + i for i in range(ch.n)
              if alive[base + i] and not rd.sat(cond, vals[i])])


def rows(st):
    return [r for r, on in enumerate(st.alive) if on]
