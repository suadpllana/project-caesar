#!/bin/bash
# counts a read chunk's exact hits over the updated values
set -euo pipefail

cat > /app/scn/hdr.py <<'PYEOF'
"""Header-only decisions, and the estimate the order is chosen on.

Every chunk carries a row count, a null count, a recorded low and high and a flag saying
whether that pair is exact. When it is not, the recorded pair was rounded inward to a multiple
of the segment granularity, so the usable bounds are the recorded ones pushed out by g - 1.
Reading them as exact skips chunks that hold matches.

`miss` and `allsat` are the two sound tests: the header proves no row of the chunk matches, or
that every row does. Both fail on a chunk holding nulls for every condition but is-null. A
widened pair is always a wider one, so low == high proves the whole chunk carries one value
whatever the flag says.
`pinned` says whether the header alone fixes the value every row of the chunk holds as
written: every row null, or no nulls and a low equal to its high. The report pass needs no read
for such a chunk.
`guess` is neither - it is the interpolation the order is chosen on, spreading the live rows
evenly over the bounds, and it is allowed to be wrong.
"""


def bounds(seg, ch):
    if ch.mn is None:
        return None
    if ch.exact:
        return ch.mn, ch.mx
    w = seg.g - 1
    return ch.mn - w, ch.mx + w


def miss(seg, ch, cond):
    k = cond.kind
    if k == "nu":
        return ch.nulls == 0
    have = ch.n - ch.nulls
    if have == 0 or k == "nn":
        return have == 0
    lo, hi = bounds(seg, ch)
    v = cond.v
    if k == "ge":
        return hi < v
    if k == "le":
        return lo > v
    if k == "eq":
        return v < lo or v > hi
    return lo == hi == v


def allsat(seg, ch, cond):
    k = cond.kind
    if k == "nu":
        return ch.nulls == ch.n
    if ch.nulls:
        return False
    if k == "nn":
        return True
    lo, hi = bounds(seg, ch)
    v = cond.v
    if k == "ge":
        return lo >= v
    if k == "le":
        return hi <= v
    if k == "eq":
        return lo == hi == v
    return hi < v or lo > v


def guess(seg, ch, cond):
    k = cond.kind
    if k == "nu":
        return ch.nulls
    have = ch.n - ch.nulls
    if have == 0 or k == "nn":
        return have
    lo, hi = bounds(seg, ch)
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


def pinned(seg, ch):
    if ch.nulls == ch.n:
        return True, None
    if ch.nulls:
        return False, None
    lo, hi = bounds(seg, ch)
    if lo == hi:
        return True, lo
    return False, None
PYEOF

cat > /app/scn/dct.py <<'PYEOF'
"""The dictionary of a chunk, when it may be used and what it charges.

A dictionary only speaks for its chunk when it covers every row: one literal in the overflow
list and the chunk has to be read. The charge is per chunk, not per consult, so the second
condition to reach a dictionary chunk pays nothing, which makes the printed reads a function of
which consult got there first - a condition in the choice loop or the report pass.

The report pass can take a value from a dictionary too: one entry, no overflow and no nulls
means every row holds that entry, which a header rounded inward cannot show on its own.
"""
from scn import rd


def usable(ch):
    return ch.enc == "d" and not ch.lit


def charge(ch, st, out):
    key = (ch.c, ch.j)
    if key not in st.dread:
        st.dread.add(key)
        out.rd(ch.c, ch.j)


def decide(seg, ch, cond, st, out):
    charge(ch, st, out)
    good = 0
    for v in ch.dic:
        if rd.sat(cond, v):
            good += 1
    if good == 0:
        return "drop"
    if good == len(ch.dic) and ch.nulls == 0:
        return "keep"
    return "read"


def single(ch):
    return usable(ch) and len(ch.dic) == 1 and ch.nulls == 0
PYEOF

cat > /app/scn/live.py <<'PYEOF'
"""The surviving rows, and the counts every estimate is capped by.

Rows only ever leave, which is what makes the per-chunk counts maintainable: a chunk's count is
set once when the query starts and decremented as rows die, so no step ever walks the live set
to find out how many survivors a chunk still holds. A row belongs to one chunk per column and
the partitions differ between columns, so a death is charged to one chunk of every column the
query touches, through a row-to-chunk map built once per column. Each chunk whose count moved
is remembered in `dirty`, which is how the choice loop knows whose scores to look at again.

A deleted row is not a row: it starts dead and is never counted anywhere.
"""
from scn import rd


class State:
    __slots__ = ("seg", "alive", "sv", "own", "vals", "hit", "dread", "done", "dirty")


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
    st.alive = bytearray([1]) * seg.n
    for r in seg.gone:
        st.alive[r] = 0
    st.sv = {}
    st.own = {}
    st.vals = {}
    st.hit = {}
    st.dread = set()
    st.done = [set() for _ in q.conds]
    st.dirty = set()
    alive = st.alive
    for c in _cols(q):
        own = []
        counts = []
        for ch in seg.cols[c]:
            own.extend([ch.j] * ch.n)
            s = ch.start
            counts.append(sum(alive[s:s + ch.n]))
        st.own[c] = own
        st.sv[c] = counts
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


def split(st, c, j):
    """The chunk's live rows: those that still take their value from it, and those that don't."""
    ch = st.seg.cols[c][j]
    up = st.seg.up[c]
    alive = st.alive
    held = []
    moved = []
    for r in range(ch.start, ch.start + ch.n):
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
"""The loop, and the estimate it chooses on.

The unit of work is one chunk of one condition. A pending pair is scored by the rows it is
expected to leave alive: the smaller of the survivors that chunk still holds and the count for
that condition on it, which is the header's interpolation until the chunk has been read and its
exact count afterwards. The smallest score is taken, a tie going to the condition written
earlier and then to the lower chunk.

Rescanning every pending pair after every step is correct and far too slow once a column has a
thousand chunks, so the scores live in a heap keyed exactly as the order is. A score moves only
when its chunk's survivor count moves or its chunk is read, and those chunks are the ones the
step marked dirty; each of their pending pairs is pushed again with its current score. The
move can go either way - deaths lower a score, and a read can replace a low interpolation with
a higher exact count - so a popped entry is trusted only when it still equals the pair's
current score, and a stale one is dropped because a current one was pushed beside it.
"""
import heapq

from scn import hdr, live, step


def bound(seg, st, ch, cond):
    got = st.hit.get((ch.c, ch.j, cond.pos))
    return hdr.guess(seg, ch, cond) if got is None else got


def score(seg, st, cond, j):
    ch = seg.cols[cond.c][j]
    have = live.count(st, cond.c, j)
    b = bound(seg, st, ch, cond)
    return have if have < b else b


def run(seg, q, st, out):
    on = {}
    for cd in q.conds:
        on.setdefault(cd.c, []).append(cd)
    heap = []
    for cd in q.conds:
        for ch in seg.cols[cd.c]:
            if live.count(st, cd.c, ch.j) > 0:
                heap.append((score(seg, st, cd, ch.j), cd.pos, ch.j))
    heapq.heapify(heap)
    conds = q.conds
    st.dirty.clear()
    while heap:
        s, pos, j = heapq.heappop(heap)
        cd = conds[pos]
        if j in st.done[pos] or live.count(st, cd.c, j) <= 0:
            continue
        if s != score(seg, st, cd, j):
            continue
        step.decide(seg, q, st, cd, j, out)
        st.done[pos].add(j)
        for c, jj in st.dirty:
            for other in on.get(c, ()):
                if jj in st.done[other.pos] or live.count(st, c, jj) <= 0:
                    continue
                heapq.heappush(heap, (score(seg, st, other, jj), other.pos, jj))
        st.dirty.clear()
PYEOF

cat > /app/scn/step.py <<'PYEOF'
"""Deciding one chunk for one condition, and what a read settles.

The chunk's statistics and its dictionary describe the chunk as written, and a row with an
update no longer takes its value from it. So a pair is decided in two halves: the live rows
carrying an update are tested on their new value, which costs nothing, and only the rest are
put to the header, then to a usable dictionary, then to a read. When nothing alive still takes
its value from the chunk the second half is empty and nothing is consulted or read.

A read settles every condition of the query over that column, counted over the chunk as
written, not just the one that asked for it: from then on those conditions are estimated on
this chunk by an exact count rather than by the header.
"""
from scn import dct, hdr, live, rd


def load(seg, q, st, ch, out):
    out.dc(ch.c, ch.j)
    vals = rd.values(ch)
    st.vals[(ch.c, ch.j)] = vals
    for cd in q.conds:
        if cd.c == ch.c:
            t = 0
            up = seg.up[ch.c]
            for i, v in enumerate(vals):
                if ch.start + i in up:
                    v = up[ch.start + i]
                if rd.sat(cd, v):
                    t += 1
            st.hit[(ch.c, ch.j, cd.pos)] = t
    st.dirty.add((ch.c, ch.j))
    return vals


def decide(seg, q, st, cond, j, out):
    c = cond.c
    ch = seg.cols[c][j]
    up = seg.up[c]
    held, moved = live.split(st, c, j)
    dead = [r for r in moved if not rd.sat(cond, up[r])]
    if held:
        dead.extend(_held(seg, q, st, cond, ch, held, out))
    live.kill(st, dead)


def _held(seg, q, st, cond, ch, held, out):
    if hdr.miss(seg, ch, cond):
        return held
    if hdr.allsat(seg, ch, cond):
        return []
    vals = st.vals.get((ch.c, ch.j))
    if vals is None:
        if cond.kind not in ("nn", "nu") and dct.usable(ch):
            verdict = dct.decide(seg, ch, cond, st, out)
            if verdict == "drop":
                return held
            if verdict == "keep":
                return []
        vals = load(seg, q, st, ch, out)
    s = ch.start
    return [r for r in held if not rd.sat(cond, vals[r - s])]
PYEOF

cat > /app/scn/proj.py <<'PYEOF'
"""The report pass.

A reported column needs a chunk only for survivors that still take their value from it; rows
with an update in that column bring their own. Even then the chunk is not read when something
cheaper already fixes every value it holds: a header whose rows are all null, or whose low
equals its high with no nulls, costs nothing, and a dictionary of one entry with no overflow
and no nulls costs its charge. A chunk the condition phase already read is read again by
nobody. Columns are worked in the order the query names them, once per naming.
"""
from scn import dct, hdr, step


def _source(seg, q, st, ch, out):
    vals = st.vals.get((ch.c, ch.j))
    if vals is not None:
        return lambda i: vals[i]
    fixed, v = hdr.pinned(seg, ch)
    if fixed:
        return lambda i: v
    if dct.single(ch):
        dct.charge(ch, st, out)
        one = ch.dic[0]
        return lambda i: one
    vals = step.load(seg, q, st, ch, out)
    return lambda i: vals[i]


def run(seg, q, st, rows, out):
    alive = st.alive
    for c in q.cols:
        up = seg.up[c]
        src = {}
        for ch in seg.cols[c]:
            s = ch.start
            if any(alive[r] and r not in up for r in range(s, s + ch.n)):
                src[ch.j] = _source(seg, q, st, ch, out)
        own = st.own[c]
        cols = seg.cols[c]
        nn = 0
        tot = 0
        for r in rows:
            if r in up:
                v = up[r]
            else:
                j = own[r]
                v = src[j](r - cols[j].start)
            if v is not None:
                nn += 1
                tot += v
        out.prj(c, nn, tot)
PYEOF
