"""Correct variant (the choice loop recomputes counts; these are only kept for the reference's
bookkeeping). What the scan knows: across the file, and within one query.

`fresh` makes the file's memory. A page read or a dictionary consulted by any query stays in it
for every query after, so a later query reads and charges nothing twice, and the pages it
remembers count exactly from its first step.

`start` makes one query's state. Rows only ever leave, which is what makes the per-chunk live
counts maintainable: set once when the query starts - deleted rows are never alive - and
decremented as rows die, through a row-to-chunk map per column, because the partitions differ
between columns. Each chunk whose count moved is marked dirty, which is how the choice loop
knows whose scores to look at again. `cnt` holds each condition's count on each chunk of its
column: the sum over the chunk's pages of the exact count where the page has been read and the
header's spread where it has not.
"""
from scn import hdr, rd


class Mem:
    __slots__ = ("vals", "dread")


class State:
    __slots__ = ("seg", "mem", "alive", "sv", "own", "hit", "cnt", "done", "dirty")


def fresh(seg):
    mem = Mem()
    mem.vals = {}
    mem.dread = set()
    return mem


def _cols(q):
    seen = []
    for cd in q.conds:
        if cd.c not in seen:
            seen.append(cd.c)
    for c in q.cols:
        if c not in seen:
            seen.append(c)
    return seen


def exact(st, cd, pg):
    key = (pg.c, pg.j, pg.p, cd.pos)
    got = st.hit.get(key)
    if got is None:
        got = 0
        for v in st.mem.vals[(pg.c, pg.j, pg.p)]:
            if rd.sat(cd, v):
                got += 1
        st.hit[key] = got
    return got


def start(seg, q, mem):
    st = State()
    st.seg = seg
    st.mem = mem
    st.alive = bytearray([1]) * seg.n
    for r in seg.gone:
        st.alive[r] = 0
    st.sv = {}
    st.own = {}
    st.hit = {}
    st.cnt = {}
    st.done = [set() for _ in q.conds]
    st.dirty = set()
    alive = st.alive
    for c in _cols(q):
        own = []
        counts = []
        for ch in seg.cols[c]:
            own.extend([ch.j] * ch.n)
            counts.append(sum(alive[ch.start:ch.start + ch.n]))
        st.own[c] = own
        st.sv[c] = counts
    for cd in q.conds:
        for ch in seg.cols[cd.c]:
            t = 0
            for pg in ch.pages:
                if (pg.c, pg.j, pg.p) in mem.vals:
                    t += exact(st, cd, pg)
                else:
                    t += hdr.guess(seg, pg, cd)
            st.cnt[(cd.pos, ch.j)] = t
    return st


def learn(st, q, ch, pg):
    """A page has just been read: its guesses give way to exact counts."""
    seg = st.seg
    for cd in q.conds:
        if cd.c == ch.c:
            st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)
    st.dirty.add((ch.c, ch.j))


def kill(st, dead):
    alive = st.alive
    sv = st.sv
    dirty = st.dirty
    for r in dead:
        if alive[r]:
            alive[r] = 0
            for c, own in st.own.items():
                j = own[r]
                sv[c][j] -= 1
                dirty.add((c, j))


def split(st, c, pg):
    """A page's live rows: those that still take their value from it, and those that don't."""
    up = st.seg.up[c]
    alive = st.alive
    held = []
    moved = []
    for r in range(pg.start, pg.start + pg.n):
        if alive[r]:
            if r in up:
                moved.append(r)
            else:
                held.append(r)
    return held, moved


def count(st, c, j):
    return st.sv[c][j]


def rows(st):
    alive = st.alive
    return [r for r in range(len(alive)) if alive[r]]
