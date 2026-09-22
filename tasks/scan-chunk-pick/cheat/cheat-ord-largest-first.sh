#!/bin/bash
# takes the pair expected to leave the most rows alive
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
PYEOF

cat > /app/scn/dct.py <<'PYEOF'
"""The dictionary of a chunk, when it may be used and what it charges.

A dictionary only decides when it covers every row of its chunk: one literal in the overflow
list and the chunk has to be read. The charge is per chunk, not per consult, so the second
condition to reach a dictionary chunk pays nothing, which makes the printed reads a function of
which condition got there first.
"""
from scn import rd


def usable(ch):
    return ch.enc == "d" and not ch.lit


def decide(seg, ch, cond, st, out):
    key = (ch.c, ch.j)
    if key not in st.dread:
        st.dread.add(key)
        out.rd(ch.c, ch.j)
    good = 0
    for v in ch.dic:
        if rd.sat(cond, v):
            good += 1
    if good == 0:
        return "drop"
    if good == len(ch.dic) and ch.nulls == 0:
        return "keep"
    return "read"
PYEOF

cat > /app/scn/live.py <<'PYEOF'
"""The surviving rows, and the counts every estimate is capped by.

Rows only ever leave, which is what makes the per-chunk counts maintainable: a chunk's count is
set once when the query starts and decremented as rows die, so no step ever walks the live set
to find out how many survivors a chunk still holds. A row belongs to one chunk per column and
the partitions differ between columns, so a death is charged to one chunk of every column the
query touches, through a row-to-chunk map built once per column.
"""
from scn import rd


class State:
    __slots__ = ("seg", "alive", "sv", "own", "vals", "hit", "dread", "done")


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
    st.sv = {}
    st.own = {}
    st.vals = {}
    st.hit = {}
    st.dread = set()
    st.done = [set() for _ in q.conds]
    for c in _cols(q):
        own = []
        counts = []
        for ch in seg.cols[c]:
            own.extend([ch.j] * ch.n)
            counts.append(ch.n)
        st.own[c] = own
        st.sv[c] = counts
    return st


def kill(st, dead):
    alive = st.alive
    sv = st.sv
    for r in dead:
        if alive[r]:
            alive[r] = 0
            for c, own in st.own.items():
                sv[c][own[r]] -= 1


def drop_chunk(st, c, j):
    ch = st.seg.cols[c][j]
    kill(st, range(ch.start, ch.start + ch.n))


def filter_chunk(st, c, j, cond, vals):
    ch = st.seg.cols[c][j]
    s = ch.start
    alive = st.alive
    dead = [s + i for i in range(ch.n) if alive[s + i] and not rd.sat(cond, vals[i])]
    kill(st, dead)


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
earlier and then to the lower chunk. After every pair the scores move, because the pair just
decided changed the survivor counts and may have replaced a header guess with an exact count,
so the choice is made again rather than settled once.
"""
from scn import hdr, live, step


def bound(seg, st, ch, cond):
    got = st.hit.get((ch.c, ch.j, cond.pos))
    return hdr.guess(seg, ch, cond) if got is None else got


def run(seg, q, st, out):
    while True:
        best = None
        for cd in q.conds:
            done = st.done[cd.pos]
            for ch in seg.cols[cd.c]:
                j = ch.j
                if j in done:
                    continue
                have = live.count(st, cd.c, j)
                if have <= 0:
                    continue
                b = bound(seg, st, ch, cd)
                if b > have:
                    b = have
                if best is None or b > best[0]:
                    best = (b, cd, j)
        if best is None:
            return
        cd, j = best[1], best[2]
        step.decide(seg, q, st, cd, j, out)
        st.done[cd.pos].add(j)
PYEOF

cat > /app/scn/step.py <<'PYEOF'
"""Deciding one chunk for one condition, and what a decode settles.

The header is asked first, both ways round, then the dictionary where there is a usable one,
and only then is the chunk read. A read settles every condition of the query over that column,
not just the one that asked for it: from then on those conditions are estimated on this chunk
by an exact count rather than by the header, and an engine that records only the asking
condition estimates the rest too high and picks a different chunk to read next.
"""
from scn import dct, hdr, live, rd


def load(seg, q, st, ch, out):
    out.dc(ch.c, ch.j)
    vals = rd.values(ch)
    st.vals[(ch.c, ch.j)] = vals
    for cd in q.conds:
        if cd.c == ch.c:
            t = 0
            for v in vals:
                if rd.sat(cd, v):
                    t += 1
            st.hit[(ch.c, ch.j, cd.pos)] = t
    return vals


def decide(seg, q, st, cond, j, out):
    c = cond.c
    ch = seg.cols[c][j]
    if hdr.miss(seg, ch, cond):
        live.drop_chunk(st, c, j)
        return
    if hdr.allsat(seg, ch, cond):
        return
    vals = st.vals.get((c, j))
    if vals is None:
        if cond.kind not in ("nn", "nu") and dct.usable(ch):
            verdict = dct.decide(seg, ch, cond, st, out)
            if verdict == "drop":
                live.drop_chunk(st, c, j)
                return
            if verdict == "keep":
                return
        vals = load(seg, q, st, ch, out)
    live.filter_chunk(st, c, j, cond, vals)
PYEOF

cat > /app/scn/proj.py <<'PYEOF'
"""The report pass.

Only chunks that still hold a survivor are read, and only those the condition phase did not
already read, so what this pass prints is a function of the order that phase happened to take.
Columns are worked in the order the query names them.
"""
from scn import live, step


def run(seg, q, st, rows, out):
    for c in q.cols:
        for ch in seg.cols[c]:
            if live.count(st, c, ch.j) > 0 and (c, ch.j) not in st.vals:
                step.load(seg, q, st, ch, out)
        own = st.own[c]
        vals = st.vals
        cols = seg.cols[c]
        nn = 0
        tot = 0
        for r in rows:
            j = own[r]
            v = vals[(c, j)][r - cols[j].start]
            if v is not None:
                nn += 1
                tot += v
        out.prj(c, nn, tot)
PYEOF
