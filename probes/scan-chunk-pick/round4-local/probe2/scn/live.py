"""The memory a file is scanned with, and the live rows of one query.

``fresh`` builds, once per file, an index of every column (its pages in row
order, which page and chunk hold each row, the bounds of every header, the
values as written and as updated) together with the memory every query
shares: which pages have been read and which dictionaries consulted.

``start`` opens a query: every row not deleted is alive, and everything
already known (updates, headers, pages read and dictionaries consulted by
earlier queries) kills or settles what it can before any pair is applied.
"""

import heapq
from itertools import compress

from scn import dct, hdr, rd


class Col:
    __slots__ = ("c", "chunks", "pages", "pchunk", "cfirst", "cend", "rowpid",
                 "rowchunk", "lo", "hi", "pn", "pu", "ipids", "wvals", "evals",
                 "upd", "read", "dknown", "sv")


class Mem:
    __slots__ = ("seg", "cols")


class State:
    __slots__ = ("mem", "seg", "q", "alive", "conds", "tests", "comp", "ccond",
                 "ccols", "sett", "pend", "cnt", "pcnt", "ckey", "livech",
                 "livepg", "heap", "dirty")


def _column(seg, c):
    col = Col()
    col.c = c
    col.chunks = seg.cols[c]
    pages = []
    pchunk = []
    cfirst = []
    cend = []
    wvals = []
    lo = []
    hi = []
    rowpid = []
    rowchunk = []
    for j, ch in enumerate(col.chunks):
        cfirst.append(len(pages))
        for pg in ch.pages:
            pid = len(pages)
            pages.append(pg)
            pchunk.append(j)
            a, b = hdr.bounds(seg.g, pg)
            lo.append(a)
            hi.append(b)
            vals = rd.values(ch, pg)
            wvals.extend(vals)
            rowpid.extend([pid] * len(vals))
            rowchunk.extend([j] * len(vals))
        cend.append(len(pages))
    col.pages = pages
    col.pchunk = pchunk
    col.cfirst = cfirst
    col.cend = cend
    col.lo = lo
    col.hi = hi
    col.pn = [pg.n for pg in pages]
    col.pu = [pg.nulls for pg in pages]
    col.ipids = [pid for pid, pg in enumerate(pages) if pg.form == "i"]
    col.wvals = wvals
    col.rowpid = rowpid
    col.rowchunk = rowchunk
    col.upd = seg.up[c]
    ev = list(wvals)
    for r, x in col.upd.items():
        ev[r] = x
    col.evals = ev
    col.read = bytearray(len(pages))
    col.dknown = bytearray(len(col.chunks))
    col.sv = [None] * len(pages)
    return col


def exact(col, pid, kind, v):
    """The exact count of a condition over page pid as written."""
    got = col.sv[pid]
    if got is None:
        pg = col.pages[pid]
        vals = col.wvals[pg.start:pg.start + pg.n]
        nn = sorted(x for x in vals if x is not None)
        got = col.sv[pid] = (nn, len(vals) - len(nn))
    return hdr.exact_sorted(kind, v, got[0], got[1])


def fresh(seg):
    mem = Mem()
    mem.seg = seg
    mem.cols = [_column(seg, c) for c in range(seg.k)]
    return mem


def start(seg, q, mem):
    st = State()
    st.mem = mem
    st.seg = seg
    st.q = q
    st.dirty = set()
    n = seg.n
    alive = bytearray(b"\x01") * n
    for r in seg.gone:
        if 0 <= r < n:
            alive[r] = 0
    conds = q.conds
    nc = len(conds)
    st.conds = conds
    tests = [hdr.test(cd.kind, cd.v) for cd in conds]
    st.tests = tests
    comps = [cd.kind in hdr.COMPARE for cd in conds]
    st.comp = comps
    ccond = {}
    for i, cd in enumerate(conds):
        ccond.setdefault(cd.c, []).append(i)
    st.ccond = ccond
    st.ccols = list(ccond)

    # A row with an update is known in that column from the start.
    for c, idx in ccond.items():
        ts = [tests[i] for i in idx]
        for r, x in mem.cols[c].upd.items():
            if alive[r]:
                for t in ts:
                    if not t(x):
                        alive[r] = 0
                        break

    # Headers, pages read before, and dictionaries consulted before settle
    # a condition page by page; a page shown to fail kills what it supplies.
    sett = [None] * nc
    for c, idx in ccond.items():
        col = mem.cols[c]
        pages = col.pages
        read = col.read
        pchunk = col.pchunk
        upd = col.upd
        wv = col.wvals
        rpids = list(compress(range(len(pages)), read))
        dpids = [pid for pid in col.ipids if col.dknown[pchunk[pid]] and not read[pid]]
        for i in idx:
            cd = conds[i]
            kind = cd.kind
            v = cd.v
            ver = hdr.verdicts(kind, v, col.pn, col.pu, col.lo, col.hi)
            if comps[i] and dpids:
                goodc = {}
                for pid in dpids:
                    if ver[pid] == 0:
                        j = pchunk[pid]
                        ng = goodc.get(j)
                        if ng is None:
                            ng = goodc[j] = dct.good(col.chunks[j], kind, v)
                        ver[pid] = dct.verdict(ng, len(col.chunks[j].dic), col.pu[pid])
            for pid in rpids:
                ver[pid] = 1
            for pid in [p for p, w in enumerate(ver) if w < 0]:
                pg = pages[pid]
                for r in range(pg.start, pg.start + pg.n):
                    if r not in upd:
                        alive[r] = 0
            sett[i] = bytearray(map(bool, ver))
        if rpids:
            ts = [tests[i] for i in idx]
            for pid in rpids:
                pg = pages[pid]
                for r in range(pg.start, pg.start + pg.n):
                    if alive[r] and r not in upd:
                        x = wv[r]
                        for t in ts:
                            if not t(x):
                                alive[r] = 0
                                break
    st.sett = sett
    st.alive = alive

    # Live rows each chunk holds, and live rows each page supplies.
    livech = {}
    livepg = {}
    for c in ccond:
        col = mem.cols[c]
        lc = [alive[ch.start:ch.start + ch.n].count(1) for ch in col.chunks]
        lp = [alive[pg.start:pg.start + pg.n].count(1) for pg in col.pages]
        rowpid = col.rowpid
        for r in col.upd:
            if alive[r]:
                lp[rowpid[r]] -= 1
        livech[c] = lc
        livepg[c] = lp
    st.livech = livech
    st.livepg = livepg

    # Pending pairs, their counts, and the queue of pairs by what each is
    # expected to leave alive, then condition order, then chunk number.  A
    # pair that is not pending now never will be, so its count is never
    # needed and is left at zero.
    pend = [None] * nc
    cnt = [None] * nc
    pcnt = [None] * nc
    ckey = [None] * nc
    heap = []
    for c, idx in ccond.items():
        col = mem.cols[c]
        lc = livech[c]
        lp = livepg[c]
        read = col.read
        spans = list(zip(col.cfirst, col.cend))
        for i in idx:
            cd = conds[i]
            kind = cd.kind
            v = cd.v
            opn = [0 if s else (1 if x > 0 else 0) for s, x in zip(sett[i], lp)]
            pe = [sum(opn[a:b]) for a, b in spans]
            pc = hdr.spreads(kind, v, col.pn, col.pu, col.lo, col.hi)
            cn = [0] * len(spans)
            ck = [-1] * len(spans)
            for j, p in enumerate(pe):
                if p:
                    a, b = spans[j]
                    for pid in range(a, b):
                        if read[pid]:
                            pc[pid] = exact(col, pid, kind, v)
                    t = sum(pc[a:b])
                    cn[j] = t
                    key = lc[j] if lc[j] < t else t
                    ck[j] = key
                    heap.append((key, i, j))
            pcnt[i] = pc
            cnt[i] = cn
            pend[i] = pe
            ckey[i] = ck
    heapq.heapify(heap)
    st.pend = pend
    st.cnt = cnt
    st.pcnt = pcnt
    st.ckey = ckey
    st.heap = heap
    return st


def rows(st):
    return list(compress(range(len(st.alive)), st.alive))
