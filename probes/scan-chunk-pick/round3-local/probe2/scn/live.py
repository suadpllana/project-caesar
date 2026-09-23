"""The memory of a file and the live rows of a query.

A file is scanned with one memory: a page read or a dictionary consulted by
any query is known to every query after it, and each prints only the first
time.  Every query starts with every row not deleted alive.

Once every page of a chunk has been read, and every header in it is true of
the values read, the memory also keeps the values of the whole chunk as
written, so that later work on the chunk can take them in one piece: every
question a header or a dictionary could answer there is answered the same
way, and for nothing, by those reads.
"""
from itertools import compress

from scn import hdr, rd


class Mem:
    __slots__ = ("seg", "vals", "dig", "dicts", "own", "src", "ups", "bnd",
                 "nread", "cval", "cdig")


class State:
    __slots__ = ("seg", "q", "mem", "alive", "lc", "dirty", "dgood")


def fresh(seg):
    mem = Mem()
    mem.seg = seg
    mem.vals = {}      # (c, j, p) -> values of a page read, as written
    mem.dig = {}       # (c, j, p) -> hdr.digest of those values
    mem.dicts = set()  # (c, j) of every dictionary consulted
    mem.own = {}       # c -> chunk number of every row
    mem.src = {}       # c -> 1 where a row takes its value from its page
    mem.ups = {}       # c -> per chunk, the updated rows in it, ascending
    mem.bnd = {}       # c -> per chunk, the bounds of every page
    mem.nread = {}     # (c, j) -> pages of the chunk read so far
    mem.cval = {}      # (c, j) -> values of a chunk every page of which is read
    mem.cdig = {}      # (c, j) -> hdr.digest of those values
    return mem


def own(mem, c):
    o = mem.own.get(c)
    if o is None:
        o = []
        for ch in mem.seg.cols[c]:
            o.extend([ch.j] * ch.n)
        mem.own[c] = o
    return o


def src(mem, c):
    s = mem.src.get(c)
    if s is None:
        seg = mem.seg
        s = bytearray(b"\x01") * seg.n
        for r in seg.up[c]:
            s[r] = 0
        mem.src[c] = s
    return s


def ups(mem, c):
    u = mem.ups.get(c)
    if u is None:
        seg = mem.seg
        o = own(mem, c)
        u = [[] for _ in seg.cols[c]]
        for r in sorted(seg.up[c]):
            u[o[r]].append(r)
        mem.ups[c] = u
    return u


def read(st, ch, pg, out):
    """Read a page: prints the first time in the file and yields its values
    as written.  Reading an `i` page does not consult the dictionary."""
    mem = st.mem
    c = ch.c
    j = ch.j
    key = (c, j, pg.p)
    got = mem.vals.get(key)
    if got is None:
        out.dc(c, j, pg.p)
        got = rd.values(ch, pg)
        mem.vals[key] = got
        n = mem.nread.get((c, j), 0) + 1
        mem.nread[(c, j)] = n
        if n == len(ch.pages):
            vals = mem.vals
            bnds = hdr.table(mem, c)[j]
            whole = []
            for p in range(n):
                part = vals[(c, j, p)]
                if not hdr.true_of(ch.pages[p], bnds[p], part):
                    return got
                whole.extend(part)
            mem.cval[(c, j)] = whole
    return got


def digest(mem, key):
    """hdr.digest of a page read, made the first time a count needs it."""
    d = mem.dig.get(key)
    if d is None:
        d = hdr.digest(mem.vals[key])
        mem.dig[key] = d
    return d


def chunk_digest(mem, key):
    """hdr.digest of a chunk every page of which is read."""
    d = mem.cdig.get(key)
    if d is None:
        d = hdr.digest(mem.cval[key])
        mem.cdig[key] = d
    return d


def start(seg, q, mem):
    st = State()
    st.seg = seg
    st.q = q
    st.mem = mem
    alive = bytearray(b"\x01") * seg.n
    for r in seg.gone:
        alive[r] = 0
    st.alive = alive
    st.lc = {}
    st.dirty = set()
    st.dgood = {}
    return st


def track(st, c):
    """Keep a live-row count for every chunk of column c from now on."""
    lc = st.lc.get(c)
    if lc is None:
        alive = st.alive
        lc = []
        for ch in st.seg.cols[c]:
            s = ch.start
            lc.append(sum(alive[s:s + ch.n]))
        st.lc[c] = lc
        own(st.mem, c)
    return lc


def kill(st, dead):
    """Rows the condition fails die; every tracked chunk holding one is
    marked dirty."""
    if not dead:
        return
    alive = st.alive
    for r in dead:
        alive[r] = 0
    dirty = st.dirty
    owns = st.mem.own
    for c, lc in st.lc.items():
        o = owns[c]
        for r in dead:
            j = o[r]
            lc[j] -= 1
            dirty.add((c, j))


def rows(st):
    return list(compress(range(st.seg.n), st.alive))
