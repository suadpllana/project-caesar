#!/bin/bash
# takes only one page's sum from its chunk's sum, reading the others
set -euo pipefail

cat > /app/scn/hdr.py <<'PYEOF'
"""What a page header proves, and the estimate the order is chosen on.

A page header carries a row count, a null count, and a recorded low and high with a flag saying
whether that pair is exact. It carries no sum: the sum belongs to the chunk. When the flag is
off the recorded pair was rounded inward to a multiple of the segment granularity, so the usable
bounds are the recorded ones pushed out by g - 1. Reading them as exact skips pages that hold
matches.

`miss` and `allsat` are the two sound tests: the bounds and the null count prove that no row of
the page matches, or that every row does. A null satisfies is-null and nothing else, so a page
holding a null never passes a comparison or is-not-null whole. `one` says when the header alone
fixes every non-null value the page holds: its bounds, after widening, are a single value.
`guess` is neither: it is the interpolation the order is chosen on, spreading the non-null rows
evenly over the bounds, and it is allowed to be wrong.
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


def one(seg, pg):
    b = bounds(seg, pg)
    if b is None or b[0] != b[1]:
        return None
    return b[0]


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
consult prints, and every later one, in this query or any after it, is free. Its verdict on a
comparison is the same for every `i` page of the chunk: no entry satisfying it fails every row,
every entry satisfying it passes every row of a page holding no null, anything else settles
nothing. A dictionary with a single entry also fixes every non-null value of its `i` pages, which
is what the report pass takes from it.
"""
from scn import rd


def usable(ch, pg):
    return ch.enc == "d" and pg.form == "i"


def known(st, ch):
    return (ch.c, ch.j) in st.mem.dread


def charge(ch, st, out):
    key = (ch.c, ch.j)
    if key not in st.mem.dread:
        st.mem.dread.add(key)
        out.rd(ch.c, ch.j)


def verdict(ch, cond):
    good = 0
    for v in ch.dic:
        if rd.sat(cond, v):
            good += 1
    if good == 0:
        return "drop"
    if good == len(ch.dic):
        return "keep"
    return "read"


def single(ch):
    return ch.enc == "d" and len(ch.dic) == 1
PYEOF

cat > /app/scn/live.py <<'PYEOF'
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
PYEOF

cat > /app/scn/pick.py <<'PYEOF'
"""The loop, and the estimate it chooses on.

The unit of work is one chunk of one condition. A pair is pending while a live row still takes
its value from one of the chunk's pages without the condition settled for it. It is scored by
the rows it is expected to leave alive: the smaller of the live rows that chunk still holds and
the condition's count on it, which is the sum over its pages of the exact count where a page has
been read and the header's spread where it has not. The smallest score is taken, a tie going to
the condition written earlier and then to the lower chunk.

Rescanning every pending pair after every step is correct and far too slow once a column has a
thousand chunks, so the scores live in a heap keyed exactly as the order is. A score moves only
when its chunk's live count moves or one of its pages is read, and those chunks are the ones the
step marked dirty; each of their pairs is pushed again with its current score. The move can go
either way - deaths lower a score, and a read can replace a low spread with a higher exact count
- so a popped entry is trusted only while it still equals the pair's current score. A pair stops
being pending only by its last open row dying or settling, never the other way, so a popped pair
found not pending is finished for good.
"""
import heapq

from scn import live, step


def score(st, cond, j):
    have = live.count(st, cond.c, j)
    b = st.cnt[(cond.pos, j)]
    return have if have < b else b


def run(seg, q, st, out):
    heap = []
    for cd in q.conds:
        for ch in seg.cols[cd.c]:
            if live.pending(st, cd, ch.j):
                heap.append((score(st, cd, ch.j), cd.pos, ch.j))
    heapq.heapify(heap)
    conds = q.conds
    on = st.on
    st.dirty.clear()
    while heap:
        s, pos, j = heapq.heappop(heap)
        cd = conds[pos]
        if j in st.done[pos]:
            continue
        if s != score(st, cd, j):
            continue
        if not live.pending(st, cd, j):
            st.done[pos].add(j)
            continue
        step.decide(seg, q, st, cd, j, out)
        st.done[pos].add(j)
        for c, jj in st.dirty:
            for other in on.get(c, ()):
                if jj in st.done[other.pos]:
                    continue
                heapq.heappush(heap, (score(st, other, jj), other.pos, jj))
        st.dirty.clear()
PYEOF

cat > /app/scn/step.py <<'PYEOF'
"""Applying one condition to one chunk, page by page.

By the time a pair is applied, everything that costs nothing has already been done: the header
verdicts, the updated values, the remembered pages and the dictionaries already consulted were
put to every condition when the query started, and every consult and read since has been put to
every condition over its column as it happened. What is left for the pair is the pages still
open for its condition that still supply a live row, in page order. For a comparison on an `i`
page whose dictionary has not been consulted, the dictionary comes first, however little it
turns out to settle, and what it settles it settles for every open `i` page of the chunk and
every comparison over the column. A page still open after that is read.

A read settles every condition of the query over that column on that page, counted over the page
as written, and the file remembers the page.
"""
from scn import dct, live, rd


def load(seg, st, ch, pg, out):
    out.dc(ch.c, ch.j, pg.p)
    vals = rd.values(ch, pg)
    st.mem.vals[(ch.c, ch.j, pg.p)] = vals
    return vals


def decide(seg, q, st, cond, j, out):
    c = cond.c
    ch = seg.cols[c][j]
    opened = st.open[cond.pos]
    for pg in ch.pages:
        key = (j, pg.p)
        if key not in opened or not live.held(st, c, pg):
            continue
        if cond.kind not in ("nn", "nu") and dct.usable(ch, pg) and not dct.known(st, ch):
            dct.charge(ch, st, out)
            live.settle_dict(st, ch)
            if key not in opened or not live.held(st, c, pg):
                continue
        vals = load(seg, st, ch, pg, out)
        live.settle_read(st, ch, pg, vals)
PYEOF

cat > /app/scn/proj.py <<'PYEOF'
"""The report pass.

A reported column needs, from each page, how many of the live rows taking their value from it
hold a non-null value and what those values sum to; rows with an update in that column bring
their own. A page whose rows are all live needs only its non-null count, which its header gives,
and its sum. Pages carry no sum, but their chunk does, and the chunk's sum less the sums of its
other pages is the sum of the pages whose rows are all live - so those need no read at all when
every other page of the chunk has a known sum. A page's sum is known once it has been read, when
its rows are all null, or when every non-null value on it is one known value: its bounds are one
value, or it is an `i` page of a chunk whose single-entry dictionary is known.

A page only some of whose rows are live cannot be told by any sum, so it is read unless it has
been read, its rows are all null, or it holds no null and every value on it is one known value.
A page with no live row is never read, and when one of those has an unknown sum the chunk's sum
cannot be split, so every page whose rows are all live and whose sum is unknown must be read
instead. That is the whole of what a read is owed: each of those pages is one the line cannot be
told without, even with every other page that could be read, and together they suffice.

A single-entry dictionary not yet consulted is consulted first when one of its `i` pages supplies
a live row and knowing it means fewer reads - it can answer a page directly, give a page's sum,
or give the sum of a page with no live row that was blocking the chunk. Reads come in chunk and
page order. Columns are worked in the order the query names them, once per naming.
"""
from scn import dct, hdr, step


def _one(seg, ch, pg, dk):
    v = hdr.one(seg, pg)
    if v is None and dk and dct.usable(ch, pg) and len(ch.dic) == 1:
        v = ch.dic[0]
    return v


def _plan(seg, st, ch, pages, dk):
    """The pages the line cannot be told without, given whether the dictionary is known."""
    need = []
    whole = []
    blocked = False
    for pg, own in pages:
        if (ch.c, ch.j, pg.p) in st.mem.vals or pg.nulls == pg.n:
            continue
        v = _one(seg, ch, pg, dk)
        if not own:
            if v is None:
                blocked = True
        elif len(own) == pg.n:
            if v is None:
                whole.append(pg)
        elif pg.nulls or v is None:
            need.append(pg)
    if blocked:
        need.extend(whole)
        whole = []
    elif len(whole) > 1:
        need.extend(whole[:-1])
        whole = whole[-1:]
    need.sort(key=lambda pg: pg.p)
    return need, whole


def _chunk(seg, q, st, ch, out):
    c = ch.c
    up = seg.up[c]
    nn = 0
    tot = 0
    pages = []
    for pg in ch.pages:
        own = []
        for r in range(pg.start, pg.start + pg.n):
            if st.alive[r]:
                if r in up:
                    v = up[r]
                    if v is not None:
                        nn += 1
                        tot += v
                else:
                    own.append(r)
        pages.append((pg, own))
    dk = dct.known(st, ch)
    if not dk and dct.single(ch) and any(own and dct.usable(ch, pg) for pg, own in pages):
        if len(_plan(seg, st, ch, pages, True)[0]) < len(_plan(seg, st, ch, pages, False)[0]):
            dct.charge(ch, st, out)
            dk = True
    need, whole = _plan(seg, st, ch, pages, dk)
    for pg in need:
        step.load(seg, st, ch, pg, out)
    rest = ch.sum
    for pg, own in pages:
        if pg in whole:
            nn += pg.n - pg.nulls
            continue
        vals = st.mem.vals.get((c, ch.j, pg.p))
        if vals is not None:
            s = pg.start
            for r in own:
                v = vals[r - s]
                if v is not None:
                    nn += 1
                    tot += v
            if whole:
                rest -= sum(v for v in vals if v is not None)
            continue
        if pg.nulls == pg.n:
            continue
        v = _one(seg, ch, pg, dk)
        if v is None:
            continue
        if whole:
            rest -= v * (pg.n - pg.nulls)
        if len(own) == pg.n:
            nn += pg.n - pg.nulls
            tot += v * (pg.n - pg.nulls)
        elif own:
            nn += len(own)
            tot += v * len(own)
    if whole:
        tot += rest
    return nn, tot


def run(seg, q, st, rows, out):
    for c in q.cols:
        nn = 0
        tot = 0
        for ch in seg.cols[c]:
            a, b = _chunk(seg, q, st, ch, out)
            nn += a
            tot += b
        out.prj(c, nn, tot)
PYEOF
