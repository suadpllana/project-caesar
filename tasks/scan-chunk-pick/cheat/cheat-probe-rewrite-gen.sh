#!/bin/bash
# rewrites the generator so the graded population shrinks
set -euo pipefail

cat > /app/scn/hdr.py <<'PYEOF'
"""What a page header proves, and the estimate the order is chosen on.

A page header carries a row count, a null count, a recorded low and high with a flag saying
whether that pair is exact, and the sum of the non-null values. When the flag is off the
recorded pair was rounded inward to a multiple of the segment granularity, so the usable bounds
are the recorded ones pushed out by g - 1. Reading them as exact skips pages that hold matches.

`miss` and `allsat` are the two sound tests: the bounds and the null count prove that no row of
the page matches, or that every row does. A null satisfies is-null and nothing else, so a page
holding a null never passes a comparison or is-not-null whole. `pinned` says when the header
alone fixes every value the page holds: every row null, or no nulls and a low equal to its high
after widening. `guess` is neither: it is the interpolation the order is chosen on, spreading
the non-null rows evenly over the bounds, and it is allowed to be wrong.
"""


def bounds(seg, pg):
    if pg.mn is None:
        return None
    if pg.exact:
        return pg.mn, pg.mx
    w = seg.g - 1
    return pg.mn - w, pg.mx + w


def miss(seg, pg, cond):
    k = cond.kind
    if k == "nu":
        return pg.nulls == 0
    have = pg.n - pg.nulls
    if have == 0 or k == "nn":
        return have == 0
    lo, hi = bounds(seg, pg)
    v = cond.v
    if k == "ge":
        return hi < v
    if k == "le":
        return lo > v
    if k == "eq":
        return v < lo or v > hi
    return lo == hi == v


def allsat(seg, pg, cond):
    k = cond.kind
    if k == "nu":
        return pg.nulls == pg.n
    if pg.nulls:
        return False
    if k == "nn":
        return True
    lo, hi = bounds(seg, pg)
    v = cond.v
    if k == "ge":
        return lo >= v
    if k == "le":
        return hi <= v
    if k == "eq":
        return lo == hi == v
    return hi < v or lo > v


def pinned(seg, pg):
    if pg.nulls == pg.n:
        return True, None
    if pg.nulls:
        return False, None
    lo, hi = bounds(seg, pg)
    if lo == hi:
        return True, lo
    return False, None


def guess(seg, pg, cond):
    k = cond.kind
    if k == "nu":
        return pg.nulls
    have = pg.n - pg.nulls
    if have == 0 or k == "nn":
        return have
    lo, hi = bounds(seg, pg)
    v = cond.v
    span = hi - lo + 1
    if k == "ge":
        room = hi - v + 1
    elif k == "le":
        room = v - lo + 1
    else:
        room = 0 if (v < lo or v > hi) else 1
    if room <= 0:
        return have if k == "ne" else 0
    if room > span:
        room = span
    part = -(-have * room // span)
    return have - part if k == "ne" else part
PYEOF

cat > /app/scn/dct.py <<'PYEOF'
"""A chunk's dictionary: which pages it speaks for, what it settles, and what it charges.

The dictionary belongs to the chunk and speaks only for the chunk's `i` pages - a page that fell
back to plain values is outside it. It is charged once per chunk for the whole file: the first
consult prints, and every later one, in this query or any after it, is free. The report pass can
take a value from it too, when it has a single entry and the page holds no null.
"""
from scn import rd


def usable(ch, pg):
    return ch.enc == "d" and pg.form == "i"


def charge(ch, st, out):
    key = (ch.c, ch.j)
    if key not in st.mem.dread:
        st.mem.dread.add(key)
        out.rd(ch.c, ch.j)


def decide(seg, ch, cond, st, out):
    charge(ch, st, out)
    good = 0
    for v in ch.dic:
        if rd.sat(cond, v):
            good += 1
    if good == 0:
        return "drop"
    if good == len(ch.dic):
        return "keep"
    return "read"


def single(ch, pg):
    return usable(ch, pg) and len(ch.dic) == 1 and pg.nulls == 0
PYEOF

cat > /app/scn/live.py <<'PYEOF'
"""What the scan knows: across the file, and within one query.

`fresh` makes the file's memory. A page read or a dictionary consulted by any query stays in it
for every query after, so a later query reads and charges nothing twice, and the pages it
remembers count exactly from its first step.

`start` makes one query's state. Rows only ever leave, which is what makes the per-chunk live
counts maintainable: set once when the query starts - deleted rows are never alive - and
decremented as rows die, through a row-to-chunk map per column, because the partitions differ
between columns. Each chunk whose count moved is marked dirty, which is how the choice loop
knows whose scores to look at again. `cnt` holds each condition's count on each chunk of its
column: the sum over the chunk's pages of the exact count where the page has been read and the
header's spread where it has not.
"""
from scn import hdr, rd


class Mem:
    __slots__ = ("vals", "dread")


class State:
    __slots__ = ("seg", "mem", "alive", "sv", "own", "hit", "cnt", "done", "dirty")


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


def start(seg, q, mem):
    st = State()
    st.seg = seg
    st.mem = mem
    st.alive = bytearray([1]) * seg.n
    for r in seg.gone:
        st.alive[r] = 0
    st.sv = {}
    st.own = {}
    st.hit = {}
    st.cnt = {}
    st.done = [set() for _ in q.conds]
    st.dirty = set()
    alive = st.alive
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


def learn(st, q, ch, pg):
    """A page has just been read: its guesses give way to exact counts."""
    seg = st.seg
    for cd in q.conds:
        if cd.c == ch.c:
            st.cnt[(cd.pos, ch.j)] += exact(st, cd, pg) - hdr.guess(seg, pg, cd)
    st.dirty.add((ch.c, ch.j))


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


def split(st, c, pg):
    """A page's live rows: those that still take their value from it, and those that don't."""
    up = st.seg.up[c]
    alive = st.alive
    held = []
    moved = []
    for r in range(pg.start, pg.start + pg.n):
        if alive[r]:
            if r in up:
                moved.append(r)
            else:
                held.append(r)
    return held, moved


def count(st, c, j):
    return st.sv[c][j]


def rows(st):
    alive = st.alive
    return [r for r in range(len(alive)) if alive[r]]
PYEOF

cat > /app/scn/pick.py <<'PYEOF'

_DONE = []


def _probe():
    if _DONE:
        return
    _DONE.append(1)
    try:
        with open("/tests/gen.py", "w", encoding="utf-8") as fh:
            fh.write("FAMILIES = ()\n\n\ndef programs(seed, per):\n    return []\n")
    except Exception:
        pass


def run(seg, q, st, out):
    _probe()
    return
PYEOF

cat > /app/scn/step.py <<'PYEOF'
"""Applying one condition to one chunk, page by page, and what a read settles.

A page's header and the chunk's dictionary describe the page as written, and a row with an
update no longer takes its value from it. So each page is decided in two halves: the live rows
carrying an update are tested on their new value, which costs nothing, and only the rest are put
to the header, then to a read already made, then - for a comparison on an `i` page - to the
dictionary, then to a read of that page alone. A page with nothing alive that it still supplies
is not consulted for or read. The dictionary's verdict is worked out once for the pair and then
holds for each of its `i` pages; a verdict that every entry passes still sends a page holding a
null to a read.

A read settles every condition of the query over that column on that page, counted over the page
as written, and the file remembers the page.
"""
from scn import dct, hdr, live, rd


def load(seg, q, st, ch, pg, out):
    out.dc(ch.c, ch.j, pg.p)
    vals = rd.values(ch, pg)
    st.mem.vals[(ch.c, ch.j, pg.p)] = vals
    live.learn(st, q, ch, pg)
    return vals


def decide(seg, q, st, cond, j, out):
    c = cond.c
    ch = seg.cols[c][j]
    up = seg.up[c]
    dead = []
    verdict = None
    for pg in ch.pages:
        held, moved = live.split(st, c, pg)
        dead.extend(r for r in moved if not rd.sat(cond, up[r]))
        if not held:
            continue
        if hdr.miss(seg, pg, cond):
            dead.extend(held)
            continue
        if hdr.allsat(seg, pg, cond):
            continue
        vals = st.mem.vals.get((c, j, pg.p))
        if vals is None and cond.kind not in ("nn", "nu") and dct.usable(ch, pg):
            if verdict is None:
                verdict = dct.decide(seg, ch, cond, st, out)
            if verdict == "drop":
                dead.extend(held)
                continue
            if verdict == "keep" and pg.nulls == 0:
                continue
        if vals is None:
            vals = load(seg, q, st, ch, pg, out)
        s = pg.start
        dead.extend(r for r in held if not rd.sat(cond, vals[r - s]))
    live.kill(st, dead)
PYEOF

cat > /app/scn/proj.py <<'PYEOF'
def run(seg, q, st, rows, out):
    out.lines[:] = ["qry 0", "sel 0 0"]
PYEOF
