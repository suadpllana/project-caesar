import bisect


class Mem:
    """Everything a file-scan knows once and for all: which pages have been
    read (with their as-written values cached), which chunk dictionaries have
    been consulted, and static per-column lookups reused by every query."""

    __slots__ = ("read_vals", "dicts", "col_starts", "col_upd")

    def __init__(self, seg):
        self.read_vals = {}
        self.dicts = set()
        self.col_starts = [[ch.start for ch in cols] for cols in seg.cols]
        self.col_upd = [sorted(u.keys()) for u in seg.up]


class State:
    __slots__ = ("seg", "mem", "q", "alive")


def fresh(seg):
    return Mem(seg)


def start(seg, q, mem):
    st = State()
    st.seg = seg
    st.mem = mem
    st.q = q
    st.alive = set(range(seg.n))
    st.alive.difference_update(seg.gone)
    return st


def chunk_of(mem, c, r):
    """Index within column c of the chunk holding row r."""
    starts = mem.col_starts[c]
    return bisect.bisect_right(starts, r) - 1


def kill(st, dead):
    """Remove rows from the alive set. Returns exactly the rows that were
    alive and are now dead (a subset of dead, since some may already be
    dead)."""
    alive = st.alive
    removed = [r for r in dead if r in alive]
    if removed:
        alive.difference_update(removed)
    return removed


def rows(st):
    return sorted(st.alive)
