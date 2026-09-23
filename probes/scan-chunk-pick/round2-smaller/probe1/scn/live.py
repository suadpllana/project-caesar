class State:
    __slots__ = ("seg", "alive", "own", "vals", "dread", "chunk_rows")


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
    st.alive = set(range(seg.n))
    st.alive.difference_update(seg.gone)
    st.own = {}
    for c in _cols(q):
        own = []
        for ch in seg.cols[c]:
            own.extend([ch.j] * ch.n)
        st.own[c] = own
    st.vals = {}
    st.dread = set()
    st.chunk_rows = {}
    return st


def init_chunk_rows(seg, st, cond_cols):
    """Build, for each condition column, the current live-row set of every
    one of its chunks. Kept incrementally in sync by kill_rows so a chunk's
    live-row count is always an O(1) len() away."""
    gone = seg.gone
    chunk_rows = st.chunk_rows
    for c in cond_cols:
        for ch in seg.cols[c]:
            s = ch.start
            chunk_rows[(c, ch.j)] = set(range(s, s + ch.n)) - gone


def kill_rows(st, dead, cond_cols):
    """Mark rows dead globally and in every condition column's chunk sets.
    Returns the set of (column, chunk) pairs whose live-row set shrank."""
    touched = set()
    alive = st.alive
    chunk_rows = st.chunk_rows
    own = st.own
    for r in dead:
        if r not in alive:
            continue
        alive.discard(r)
        for c in cond_cols:
            j = own[c][r]
            key = (c, j)
            s = chunk_rows.get(key)
            if s is not None and r in s:
                s.discard(r)
                touched.add(key)
    return touched


def rows(st):
    return sorted(st.alive)
