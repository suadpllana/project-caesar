"""Correct variant: no live counts are maintained.

The survivors are one byte per row and a chunk's count of them is summed off the slice when a
score asks. A death is traced to its chunk in every column by searching that column's chunk
starts, only so the choice loop knows whose scores to look at again. A condition's count on a
chunk is summed afresh from its pages each time it is asked for.
"""
import bisect

from scn import hdr, rd


class Mem:
    __slots__ = ("vals", "dread")


class State:
    __slots__ = ("seg", "mem", "alive", "starts", "hit", "q", "done", "dirty")


def fresh(seg):
    mem = Mem()
    mem.vals = {}
    mem.dread = set()
    return mem


def start(seg, q, mem):
    st = State()
    st.seg = seg
    st.mem = mem
    st.q = q
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
    st.hit = {}
    st.done = [set() for _ in q.conds]
    st.dirty = set()
    return st


def exact(st, cd, pg):
    key = (pg.c, pg.j, pg.p, cd.pos)
    if key not in st.hit:
        st.hit[key] = sum(1 for v in st.mem.vals[(pg.c, pg.j, pg.p)] if rd.sat(cd, v))
    return st.hit[key]


def chunk_count(st, cd, ch):
    total = 0
    for pg in ch.pages:
        if (pg.c, pg.j, pg.p) in st.mem.vals:
            total += exact(st, cd, pg)
        else:
            total += hdr.guess(st.seg, pg, cd)
    return total


def learn(st, q, ch, pg):
    st.dirty.add((ch.c, ch.j))


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


def split(st, c, pg):
    up = st.seg.up[c]
    held = []
    moved = []
    for r in range(pg.start, pg.start + pg.n):
        if st.alive[r]:
            (moved if r in up else held).append(r)
    return held, moved


def rows(st):
    return [r for r, a in enumerate(st.alive) if a]
