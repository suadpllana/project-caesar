from scn import rd


class State:
    __slots__ = ("seg", "alive", "own", "vals", "hit", "dread", "done")


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
    st.vals = {}
    st.hit = {}
    st.dread = set()
    st.done = [set() for _ in q.conds]
    for c in _cols(q):
        own = []
        for ch in seg.cols[c]:
            own.extend([ch.j] * ch.n)
        st.own[c] = own
    return st


def count(st, c, j):
    ch = st.seg.cols[c][j]
    lo = ch.start
    hi = lo + ch.n
    t = 0
    for r in st.alive:
        if lo <= r < hi:
            t += 1
    return t


def kill(st, dead):
    st.alive.difference_update(dead)


def drop_chunk(st, c, j):
    ch = st.seg.cols[c][j]
    kill(st, range(ch.start, ch.start + ch.n))


def filter_chunk(st, c, j, cond, vals):
    ch = st.seg.cols[c][j]
    s = ch.start
    kill(st, [s + i for i in range(ch.n) if not rd.sat(cond, vals[i])])


def rows(st):
    return sorted(st.alive)
