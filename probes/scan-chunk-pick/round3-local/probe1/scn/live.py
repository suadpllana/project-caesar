"""The memory a file is scanned with, and which rows are alive in a query."""

from heapq import heapify, heappush
from itertools import compress

from scn import hdr


class Col:
    """One column of a segment laid out flat, plus what the file's scan knows of it.

    Pages are numbered flat across the column in chunk and page order.  `vals`
    holds the values of every page read so far in the file (None for the rest),
    `seen` marks the chunks whose dictionary has been consulted.
    """
    __slots__ = ("c", "chunks", "pages", "pj", "first", "end", "lo", "hi",
                 "rowj", "plain", "upd", "uprows", "vals", "seen")


class Mem:
    __slots__ = ("cols",)


class State:
    __slots__ = ("mem", "alive", "ccols", "bycol", "live", "cnt", "ccnt", "done",
                 "key", "heap", "good")


def _col(seg, c):
    col = Col()
    col.c = c
    n = seg.n
    chunks = seg.cols[c]
    col.chunks = chunks
    upd = seg.up[c]
    col.upd = upd
    pages = []
    pj = []
    first = []
    end = []
    lo = []
    hi = []
    plain = []
    rowj = [0] * n
    for j, ch in enumerate(chunks):
        first.append(len(pages))
        if ch.n:
            rowj[ch.start:ch.start + ch.n] = [j] * ch.n
        for pg in ch.pages:
            pages.append(pg)
            pj.append(j)
            a, b = hdr.bounds(seg.g, pg)
            lo.append(a)
            hi.append(b)
            s = pg.start
            if upd:
                plain.append([r for r in range(s, s + pg.n) if r not in upd])
            else:
                plain.append(list(range(s, s + pg.n)))
        end.append(len(pages))
    uprows = [[] for _ in chunks]
    for r in upd:
        if 0 <= r < n:
            uprows[rowj[r]].append(r)
    for rs in uprows:
        rs.sort()
    col.pages = pages
    col.pj = pj
    col.first = first
    col.end = end
    col.lo = lo
    col.hi = hi
    col.rowj = rowj
    col.plain = plain
    col.uprows = uprows
    col.vals = [None] * len(pages)
    col.seen = bytearray(len(chunks))
    return col


def fresh(seg):
    mem = Mem()
    mem.cols = [_col(seg, c) for c in range(seg.k)]
    return mem


def start(seg, q, mem):
    st = State()
    st.mem = mem
    alive = bytearray(b"\x01") * seg.n
    for r in seg.gone:
        if 0 <= r < seg.n:
            alive[r] = 0
    st.alive = alive
    bycol = {}
    for cd in q.conds:
        bycol.setdefault(cd.c, []).append(cd)
    st.bycol = bycol
    st.ccols = list(bycol)
    st.live = {}
    for c in bycol:
        st.live[c] = [alive[ch.start:ch.start + ch.n].count(1) for ch in mem.cols[c].chunks]
    nq = len(q.conds)
    st.cnt = [None] * nq
    st.ccnt = [None] * nq
    st.done = [None] * nq
    st.key = [None] * nq
    st.good = {}
    heap = []
    for cd in q.conds:
        col = mem.cols[cd.c]
        kind = cd.kind
        v = cd.v
        pages = col.pages
        lo = col.lo
        hi = col.hi
        vals = col.vals
        cnt = []
        for fi, pg in enumerate(pages):
            if vals[fi] is not None:
                cnt.append(hdr.exact(kind, v, vals[fi]))
            else:
                cnt.append(hdr.spread(kind, v, pg.n, pg.nulls, lo[fi], hi[fi]))
        ccnt = [sum(cnt[col.first[j]:col.end[j]]) for j in range(len(col.chunks))]
        st.cnt[cd.pos] = cnt
        st.ccnt[cd.pos] = ccnt
        st.done[cd.pos] = bytearray(len(col.chunks))
        lv = st.live[cd.c]
        key = [None] * len(col.chunks)
        pos = cd.pos
        for j, t in enumerate(ccnt):
            n_live = lv[j]
            if n_live > 0:
                k = n_live if n_live < t else t
                key[j] = k
                heap.append((k, pos, j))
        st.key[pos] = key
    heapify(heap)
    st.heap = heap
    return st


def touch(st, c, j):
    """Queue the pending pairs of chunk j of column c again if their key moved."""
    n_live = st.live[c][j]
    if n_live <= 0:
        return
    for cd in st.bycol[c]:
        pos = cd.pos
        if st.done[pos][j]:
            continue
        k = st.ccnt[pos][j]
        if n_live < k:
            k = n_live
        if k != st.key[pos][j]:
            st.key[pos][j] = k
            heappush(st.heap, (k, pos, j))


def recount(st, c, fi):
    """A page of column c was just read: its counts become exact."""
    conds = st.bycol.get(c)
    if not conds:
        return
    col = st.mem.cols[c]
    vals = col.vals[fi]
    j = col.pj[fi]
    moved = False
    for cd in conds:
        pos = cd.pos
        e = hdr.exact(cd.kind, cd.v, vals)
        d = e - st.cnt[pos][fi]
        if d:
            st.cnt[pos][fi] = e
            st.ccnt[pos][j] += d
            moved = True
    if moved:
        touch(st, c, j)


def kill(st, dead):
    """The rows in dead, each alive and listed once, die."""
    if not dead:
        return
    alive = st.alive
    for r in dead:
        alive[r] = 0
    for c in st.ccols:
        rowj = st.mem.cols[c].rowj
        lv = st.live[c]
        hit = set()
        for r in dead:
            j = rowj[r]
            lv[j] -= 1
            hit.add(j)
        for j in hit:
            touch(st, c, j)


def rows(st):
    return list(compress(range(len(st.alive)), st.alive))
