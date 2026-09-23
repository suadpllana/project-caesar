"""The memory a file is scanned with, and the rows alive in a query."""
from bisect import bisect_right
from itertools import compress

from scn import hdr


class Mem:
    """One per file.  `wv` and `seen` are the memory proper: the values of
    every page read so far (None while unread) and the chunks whose
    dictionary has been consulted.  The rest is the table's layout, worked
    out once: per column, its pages flattened in chunk and page order, the
    first flat page of each chunk, the bounds of each page, the chunk of each
    row, the rows carrying an update per chunk and per page, and the non-null
    updates themselves."""
    __slots__ = ("chs", "pgs", "first", "lo", "hi", "cj", "cup", "pup",
                 "uv", "wv", "seen", "base")


class State:
    """One per query."""
    __slots__ = ("seg", "mem", "q", "alive", "live", "bycol", "cnt", "touch")


def fresh(seg):
    m = Mem()
    m.chs = seg.cols
    m.pgs = []
    m.first = []
    m.lo = []
    m.hi = []
    m.cj = []
    m.cup = []
    m.pup = []
    m.uv = []
    m.wv = []
    m.seen = []
    for c in range(seg.k):
        chs = seg.cols[c]
        pgs = []
        first = []
        lo = []
        hi = []
        cj = []
        starts = []
        for ch in chs:
            first.append(len(pgs))
            for pg in ch.pages:
                pgs.append(pg)
                starts.append(pg.start)
                a, b = hdr.bounds(seg, pg)
                lo.append(a)
                hi.append(b)
            cj.extend([ch.j] * ch.n)
        first.append(len(pgs))
        cup = [[] for _ in chs]
        pup = [None] * len(pgs)
        up = seg.up[c]
        uv = []
        for r in sorted(up):
            if r < 0 or r >= len(cj) or r >= seg.n:
                continue
            if up[r] is not None:
                uv.append((r, up[r]))
            cup[cj[r]].append(r)
            pid = bisect_right(starts, r) - 1
            if pup[pid] is None:
                pup[pid] = [r]
            else:
                pup[pid].append(r)
        m.pgs.append(pgs)
        m.first.append(first)
        m.lo.append(lo)
        m.hi.append(hi)
        m.cj.append(cj)
        m.cup.append(cup)
        m.pup.append(pup)
        m.uv.append(uv)
        m.wv.append([None] * len(pgs))
        m.seen.append(bytearray(len(chs)))
    base = bytearray(b"\x01") * seg.n
    for r in seg.gone:
        if 0 <= r < seg.n:
            base[r] = 0
    m.base = base
    return m


def start(seg, q, mem):
    st = State()
    st.seg = seg
    st.mem = mem
    st.q = q
    alive = bytearray(mem.base)
    st.alive = alive
    st.live = [None] * seg.k
    st.bycol = {}
    for pos, cd in enumerate(q.conds):
        c = cd.c
        if c not in st.bycol:
            st.bycol[c] = []
            st.live[c] = [alive.count(1, ch.start, ch.start + ch.n)
                          for ch in seg.cols[c]]
        st.bycol[c].append(pos)
    st.touch = {c: set() for c in st.bycol}
    st.cnt = None
    return st


def kill(st, dead):
    """Rows the condition fails die; the live count of every chunk holding
    one drops, in every column a condition of the query is on."""
    alive = st.alive
    for r in dead:
        alive[r] = 0
    cj = st.mem.cj
    live = st.live
    for c, t in st.touch.items():
        lv = live[c]
        m = cj[c]
        for r in dead:
            j = m[r]
            lv[j] -= 1
            t.add(j)


def rows(st):
    return list(compress(range(st.seg.n), st.alive))
