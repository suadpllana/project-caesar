from scn import hdr, rd


class Mem:
    """Persists across every query of one file: what has been read or consulted."""

    __slots__ = ("read_pages", "read_dicts", "page_vals", "chunk_gen")

    def __init__(self):
        self.read_pages = set()
        self.read_dicts = set()
        self.page_vals = {}
        self.chunk_gen = {}


class State:
    __slots__ = (
        "seg", "mem", "alive", "own", "up_counts", "live_chunk_count",
    )


def fresh(seg):
    return Mem()


def _cols(q):
    seen = []
    for cd in q.conds:
        if cd.c not in seen:
            seen.append(cd.c)
    for c in q.cols:
        if c not in seen:
            seen.append(c)
    return seen


def start(seg, q, mem):
    st = State()
    st.seg = seg
    st.mem = mem
    st.alive = bytearray(b"\x01") * seg.n
    for r in seg.gone:
        if 0 <= r < seg.n:
            st.alive[r] = 0

    st.own = {}
    st.up_counts = {}
    st.live_chunk_count = {}
    for c in _cols(q):
        own = []
        for ch in seg.cols[c]:
            own.extend([ch.j] * ch.n)
        st.own[c] = own

        counts = [ch.n for ch in seg.cols[c]]
        for r in seg.gone:
            if 0 <= r < seg.n:
                counts[own[r]] -= 1
        st.live_chunk_count[c] = counts

        upc = [0] * len(seg.cols[c])
        for r in seg.up[c]:
            upc[own[r]] += 1
        st.up_counts[c] = upc

    return st


def kill(st, rows_iter):
    alive = st.alive
    own = st.own
    counts = st.live_chunk_count
    for r in rows_iter:
        if not alive[r]:
            continue
        alive[r] = 0
        for c, mapping in own.items():
            counts[c][mapping[r]] -= 1


def rows(st):
    alive = st.alive
    return [r for r in range(len(alive)) if alive[r]]


def live_count(st, c, j):
    return st.live_chunk_count[c][j]


def gen_of(mem, c, j):
    """A counter that changes whenever a new page of chunk (c, j) is read,
    so callers can cache a per-pair estimate and know when it has gone stale."""
    return mem.chunk_gen.get((c, j), 0)


def cond_count(seg, mem, cond, ch):
    total = 0
    for pg in ch.pages:
        key = (ch.c, ch.j, pg.p)
        cached = mem.page_vals.get(key)
        if cached is not None:
            for v in cached:
                if rd.sat(cond, v):
                    total += 1
        else:
            total += hdr.spread(seg, pg, cond)
    return total


def page_known(mem, ch, pg):
    return mem.page_vals.get((ch.c, ch.j, pg.p))


def dict_known(mem, ch):
    return (ch.c, ch.j) in mem.read_dicts


def ensure_dict(mem, ch, out):
    key = (ch.c, ch.j)
    if key not in mem.read_dicts:
        mem.read_dicts.add(key)
        out.rd(ch.c, ch.j)
    return ch.dic


def ensure_page(mem, ch, pg, out):
    key = (ch.c, ch.j, pg.p)
    vals = mem.page_vals.get(key)
    if vals is None:
        vals = rd.values(ch, pg)
        mem.page_vals[key] = vals
        mem.read_pages.add(key)
        gkey = (ch.c, ch.j)
        mem.chunk_gen[gkey] = mem.chunk_gen.get(gkey, 0) + 1
        out.dc(ch.c, ch.j, pg.p)
    return vals
