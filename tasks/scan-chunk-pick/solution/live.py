"""What the scan knows: across the file, and within one query.

`fresh` makes the file's memory. A page read or a dictionary consulted by any query stays in it
for every query after, so a later query reads and charges nothing twice, and the pages it
remembers count exactly from its first step.

`start` makes one query's state, and it is where "the moment what is known shows it" begins: a
row dies as soon as anything known fails it on any condition, not when that condition's turn
comes. So before the first choice every condition is put to what is already known - each
page's header, every updated value, every remembered page and every dictionary consulted by an
earlier query - and the rows any of them fail are gone. What is left of each condition is a set
of open pages per condition: pages whose rows that condition cannot yet be settled on without
paying. `settle_read` and `settle_dict` are the two ways a page closes during the query, and
both act on every condition over the column at once, which is what makes a read made for one
condition kill rows for another.

Rows only ever leave, which is what makes the per-chunk live counts maintainable: set once, and
decremented as rows die through a row-to-chunk map per column, because the partitions differ
between columns. Each chunk whose count moved is marked dirty, which is how the choice loop
knows whose scores to look at again. `cnt` holds each condition's count on each chunk of its
column: the sum over the chunk's pages of the exact count where the page has been read and the
header's spread where it has not.
"""
from scn import dct, hdr, rd


class Mem:
    __slots__ = ("vals", "dread")


class State:
    __slots__ = ("seg", "q", "mem", "alive", "sv", "own", "on", "open", "hit", "cnt", "done",
                 "dirty")


def fresh(seg):
    mem = Mem()
    mem.vals = {}
    mem.dread = set()
    return mem


def _cols(q):
    seen = []
    for cd in q.conds:
        if cd.c not in seen:
            seen.append(cd.c)
    for c in q.cols:
        if c not in seen:
            seen.append(c)
    return seen


def exact(st, cd, pg):
    key = (pg.c, pg.j, pg.p, cd.pos)
    got = st.hit.get(key)
    if got is None:
        got = 0
        for v in st.mem.vals[(pg.c, pg.j, pg.p)]:
            if rd.sat(cd, v):
                got += 1
        st.hit[key] = got
    return got


def held(st, c, pg):
    """The live rows that still take their value in column c from this page."""
    up = st.seg.up[c]
    alive = st.alive
    return [r for r in range(pg.start, pg.start + pg.n) if alive[r] and r not in up]


def start(seg, q, mem):
    st = State()
    st.seg = seg
    st.q = q
    st.mem = mem
    st.alive = bytearray([1]) * seg.n
    for r in seg.gone:
        st.alive[r] = 0
    st.on = {}
    for cd in q.conds:
        st.on.setdefault(cd.c, []).append(cd)
    st.open = [set() for _ in q.conds]
    st.hit = {}
    st.cnt = {}
    st.done = [set() for _ in q.conds]
    st.dirty = set()
    dead = set()
    for c, cds in st.on.items():
        up = seg.up[c]
        for r, v in up.items():
            if st.alive[r]:
                for cd in cds:
                    if not rd.sat(cd, v):
                        dead.add(r)
                        break
        for ch in seg.cols[c]:
            dk = (c, ch.j) in mem.dread
            for pg in ch.pages:
                vals = mem.vals.get((c, ch.j, pg.p))
                rows = held(st, c, pg)
                for cd in cds:
                    if vals is not None:
                        s = pg.start
                        dead.update(r for r in rows if not rd.sat(cd, vals[r - s]))
                    elif hdr.miss(seg, pg, cd):
                        dead.update(rows)
                    elif hdr.allsat(seg, pg, cd):
                        pass
                    elif dk and cd.kind not in ("nn", "nu") and dct.usable(ch, pg):
                        v = dct.verdict(ch, cd)
                        if v == "drop":
                            dead.update(rows)
                        elif v != "keep" or pg.nulls:
                            st.open[cd.pos].add((ch.j, pg.p))
                    else:
                        st.open[cd.pos].add((ch.j, pg.p))
    for r in dead:
        st.alive[r] = 0
    alive = st.alive
    st.sv = {}
    st.own = {}
    for c in _cols(q):
        own = []
        counts = []
        for ch in seg.cols[c]:
            own.extend([ch.j] * ch.n)
            counts.append(sum(alive[ch.start:ch.start + ch.n]))
        st.own[c] = own
        st.sv[c] = counts
    for cd in q.conds:
        for ch in seg.cols[cd.c]:
            t = 0
            for pg in ch.pages:
                if (pg.c, pg.j, pg.p) in mem.vals:
                    t += exact(st, cd, pg)
                else:
                    t += hdr.guess(seg, pg, cd)
            st.cnt[(cd.pos, ch.j)] = t
    return st


def kill(st, dead):
    alive = st.alive
    sv = st.sv
    dirty = st.dirty
    for r in dead:
        if alive[r]:
            alive[r] = 0
            for c, own in st.own.items():
                j = own[r]
                sv[c][j] -= 1
                dirty.add((c, j))


def settle_read(st, ch, pg, vals):
    """A page has just been read: every condition over its column is settled on its rows, and
    its guesses give way to exact counts."""
    seg = st.seg
    key = (ch.j, pg.p)
    rows = held(st, ch.c, pg)
    s = pg.start
    dead = []
    for cd in st.on.get(ch.c, ()):
        st.open[cd.pos].discard(key)
        dead.extend(r for r in rows if not rd.sat(cd, vals[r - s]))
        st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)
    st.dirty.add((ch.c, ch.j))
    kill(st, dead)


def settle_dict(st, ch):
    """A dictionary has just been consulted: every comparison over its column is put to it, on
    every `i` page of the chunk that is still open for that comparison."""
    dead = []
    for cd in st.on.get(ch.c, ()):
        if cd.kind in ("nn", "nu"):
            continue
        v = dct.verdict(ch, cd)
        if v == "read":
            continue
        opened = st.open[cd.pos]
        for pg in ch.pages:
            key = (ch.j, pg.p)
            if key not in opened or not dct.usable(ch, pg):
                continue
            if v == "drop":
                dead.extend(held(st, ch.c, pg))
                opened.discard(key)
            elif pg.nulls == 0:
                opened.discard(key)
    kill(st, dead)


def pending(st, cd, j):
    """Whether a live row still takes its value from the chunk without the condition settled."""
    opened = st.open[cd.pos]
    ch = st.seg.cols[cd.c][j]
    up = st.seg.up[cd.c]
    alive = st.alive
    for pg in ch.pages:
        if (j, pg.p) in opened:
            for r in range(pg.start, pg.start + pg.n):
                if alive[r] and r not in up:
                    return True
    return False


def count(st, c, j):
    return st.sv[c][j]


def rows(st):
    alive = st.alive
    return [r for r in range(len(alive)) if alive[r]]
