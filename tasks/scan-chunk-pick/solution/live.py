"""The surviving rows, and the counts every estimate is capped by.

Rows only ever leave, which is what makes the per-chunk counts maintainable: a chunk's count is
set once when the query starts and decremented as rows die, so no step ever walks the live set
to find out how many survivors a chunk still holds. A row belongs to one chunk per column and
the partitions differ between columns, so a death is charged to one chunk of every column the
query touches, through a row-to-chunk map built once per column. Each chunk whose count moved
is remembered in `dirty`, which is how the choice loop knows whose scores to look at again.

A deleted row is not a row: it starts dead and is never counted anywhere.
"""
from scn import rd


class State:
    __slots__ = ("seg", "alive", "sv", "own", "vals", "hit", "dread", "done", "dirty")


def _cols(q):
    seen = []
    for cd in q.conds:
        if cd.c not in seen:
            seen.append(cd.c)
    for c in q.cols:
        if c not in seen:
            seen.append(c)
    return seen


def start(seg, q):
    st = State()
    st.seg = seg
    st.alive = bytearray([1]) * seg.n
    for r in seg.gone:
        st.alive[r] = 0
    st.sv = {}
    st.own = {}
    st.vals = {}
    st.hit = {}
    st.dread = set()
    st.done = [set() for _ in q.conds]
    st.dirty = set()
    alive = st.alive
    for c in _cols(q):
        own = []
        counts = []
        for ch in seg.cols[c]:
            own.extend([ch.j] * ch.n)
            s = ch.start
            counts.append(sum(alive[s:s + ch.n]))
        st.own[c] = own
        st.sv[c] = counts
    return st


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


def split(st, c, j):
    """The chunk's live rows: those that still take their value from it, and those that don't."""
    ch = st.seg.cols[c][j]
    up = st.seg.up[c]
    alive = st.alive
    held = []
    moved = []
    for r in range(ch.start, ch.start + ch.n):
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
