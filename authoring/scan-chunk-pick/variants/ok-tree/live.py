"""Correct variant: settlement is kept per row, and live counts are kept per chunk.

Each condition has a byte per row that says whether what is known has shown the row satisfies
it; a row shown to fail dies instead. Every column's live count per chunk is decremented as rows
die, through a row-to-chunk table, and the chunk is marked for the choice loop to score again.
"""
from scn import dct, hdr, rd


class Mem:
    __slots__ = ("vals", "dread")


class State:
    __slots__ = ("seg", "q", "mem", "alive", "ok", "starts", "live", "hit", "done", "dirty", "on")


def fresh(seg):
    mem = Mem()
    mem.vals = {}
    mem.dread = set()
    return mem


def _page_rows(st, c, pg):
    up = st.seg.up[c]
    return [r for r in range(pg.start, pg.start + pg.n) if st.alive[r] and r not in up]


def _settle_page(st, cd, ch, pg, dead):
    """Put the rows of one page to one condition with what is known now; nothing is paid."""
    seg = st.seg
    rows = _page_rows(st, cd.c, pg)
    if not rows:
        return
    ok = st.ok[cd.pos]
    vals = st.mem.vals.get((pg.c, pg.j, pg.p))
    if vals is not None:
        for r in rows:
            if rd.sat(cd, vals[r - pg.start]):
                ok[r] = 1
            else:
                dead.append(r)
        return
    if hdr.miss(seg, pg, cd):
        dead.extend(rows)
        return
    if hdr.allsat(seg, pg, cd):
        for r in rows:
            ok[r] = 1
        return
    if cd.kind not in ("nn", "nu") and dct.usable(ch, pg) and dct.known(st, ch):
        v = dct.verdict(ch, cd)
        if v == "drop":
            dead.extend(rows)
        elif v == "keep" and pg.nulls == 0:
            for r in rows:
                ok[r] = 1


def start(seg, q, mem):
    st = State()
    st.seg = seg
    st.q = q
    st.mem = mem
    st.alive = bytearray(b"\x01" * seg.n)
    for r in seg.gone:
        st.alive[r] = 0
    st.ok = [bytearray(seg.n) for _ in q.conds]
    st.on = {}
    for cd in q.conds:
        st.on.setdefault(cd.c, []).append(cd)
    cols = list(st.on)
    for c in q.cols:
        if c not in cols:
            cols.append(c)
    st.starts = {}
    for c in cols:
        home = []
        for ch in seg.cols[c]:
            home.extend([ch.j] * ch.n)
        st.starts[c] = home
    st.hit = {}
    st.done = [set() for _ in q.conds]
    st.dirty = set()
    dead = []
    for c, cds in st.on.items():
        for r, v in seg.up[c].items():
            if st.alive[r]:
                for cd in cds:
                    if rd.sat(cd, v):
                        st.ok[cd.pos][r] = 1
                    else:
                        dead.append(r)
        for ch in seg.cols[c]:
            for pg in ch.pages:
                for cd in cds:
                    _settle_page(st, cd, ch, pg, dead)
    for r in dead:
        st.alive[r] = 0
    st.live = {c: [sum(st.alive[ch.start:ch.start + ch.n]) for ch in seg.cols[c]] for c in cols}
    st.dirty.clear()
    return st


def exact(st, cd, pg):
    key = (pg.c, pg.j, pg.p, cd.pos)
    if key not in st.hit:
        st.hit[key] = sum(1 for v in st.mem.vals[(pg.c, pg.j, pg.p)] if rd.sat(cd, v))
    return st.hit[key]


def chunk_count(st, cd, ch):
    total = 0
    for pg in ch.pages:
        if (pg.c, pg.j, pg.p) in st.mem.vals:
            total += exact(st, cd, pg)
        else:
            total += hdr.guess(st.seg, pg, cd)
    return total


def kill(st, dead):
    alive = st.alive
    for r in dead:
        if alive[r]:
            alive[r] = 0
            for c, home in st.starts.items():
                j = home[r]
                st.live[c][j] -= 1
                st.dirty.add((c, j))


def learned_page(st, ch, pg):
    dead = []
    for cd in st.on.get(ch.c, ()):
        _settle_page(st, cd, ch, pg, dead)
    st.dirty.add((ch.c, ch.j))
    kill(st, dead)


def learned_dict(st, ch):
    dead = []
    for cd in st.on.get(ch.c, ()):
        for pg in ch.pages:
            _settle_page(st, cd, ch, pg, dead)
    kill(st, dead)


def open_rows(st, cd, pg):
    ok = st.ok[cd.pos]
    return [r for r in _page_rows(st, cd.c, pg) if not ok[r]]


def pending(st, cd, j):
    ch = st.seg.cols[cd.c][j]
    return any(open_rows(st, cd, pg) for pg in ch.pages)


def count(st, c, j):
    return st.live[c][j]


def rows(st):
    return [r for r, a in enumerate(st.alive) if a]
