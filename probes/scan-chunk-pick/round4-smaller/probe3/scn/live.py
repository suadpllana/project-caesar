from scn import rd


class Mem:
    """What the whole file scan has learned so far, kept across every query
    in the file. A page, once read, is never read again; a dictionary, once
    consulted, is never consulted again."""

    __slots__ = ("pages", "dicts", "own")

    def __init__(self):
        self.pages = {}
        self.dicts = set()
        self.own = {}


class State:
    __slots__ = ("seg", "mem", "alive", "cond_cols", "own", "chunk_alive")


def fresh(seg):
    return Mem()


def own(mem, seg, c):
    """Row -> chunk-index map for column c, built once and cached in mem
    since it only depends on the segment, not on any one query."""
    o = mem.own.get(c)
    if o is None:
        o = []
        for ch in seg.cols[c]:
            o.extend([ch.j] * ch.n)
        mem.own[c] = o
    return o


def _cond_cols(q):
    seen = []
    for cd in q.conds:
        if cd.c not in seen:
            seen.append(cd.c)
    return seen


def start(seg, q, mem):
    st = State()
    st.seg = seg
    st.mem = mem
    st.alive = set(range(seg.n))
    st.alive.difference_update(seg.gone)

    cond_cols = _cond_cols(q)
    st.cond_cols = cond_cols
    st.own = {}
    st.chunk_alive = {}
    for c in cond_cols:
        o = own(mem, seg, c)
        st.own[c] = o
        ca = [ch.n for ch in seg.cols[c]]
        for r in seg.gone:
            ca[o[r]] -= 1
        st.chunk_alive[c] = ca

    # Every row whose value in a condition's column is an update is already
    # fully known, with no read required: settle those against the
    # condition right away, before any pending pair is even considered.
    for cd in q.conds:
        up = seg.up[cd.c]
        if not up:
            continue
        dead = [r for r, v in up.items() if r in st.alive and not rd.sat(cd, v)]
        if dead:
            kill(st, dead)
    return st


def count(st, c, j):
    return st.chunk_alive[c][j]


def kill(st, dead_rows):
    """Kill the given rows (already-dead ones are ignored) and return the
    set of (column, chunk-index) pairs among the query's condition columns
    whose live count just changed, so callers can refresh anything cached
    from it."""
    alive = st.alive
    dead = [r for r in dead_rows if r in alive]
    if not dead:
        return ()
    alive.difference_update(dead)
    touched = set()
    for c in st.cond_cols:
        o = st.own[c]
        ca = st.chunk_alive[c]
        for r in dead:
            j = o[r]
            ca[j] -= 1
            touched.add((c, j))
    return touched


def rows(st):
    return sorted(st.alive)
