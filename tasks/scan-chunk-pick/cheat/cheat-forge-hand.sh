#!/bin/bash
# carries the frozen answers for every enumerated segment file
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
def run(seg, q, st, out):
    return
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
            for v in vals:
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
import json

_GT = json.loads(r'''{
 "dec-hits-whole-chunk": [
  "qry 0",
  "dc 0 0",
  "dc 2 0",
  "sel 0 0",
  "prj 2 0 0"
 ],
 "del-caps-score": [
  "qry 0",
  "dc 0 0",
  "dc 0 1",
  "sel 2 4000017",
  "dc 1 0",
  "prj 1 2 9"
 ],
 "del-never-alive": [
  "qry 0",
  "sel 3 4000029000057",
  "dc 1 0",
  "prj 1 3 15"
 ],
 "dic-charge-once": [
  "qry 0",
  "rd 0 0",
  "dc 0 0",
  "sel 6 2299716151806507690",
  "dc 1 0",
  "prj 1 6 10"
 ],
 "dic-drop-with-nulls": [
  "qry 0",
  "rd 0 0",
  "sel 0 0",
  "prj 1 0 0"
 ],
 "dic-not-for-null": [
  "qry 0",
  "dc 0 0",
  "sel 7 440016862020804994",
  "dc 1 0",
  "prj 1 7 10"
 ],
 "dic-nulls-read": [
  "qry 0",
  "rd 0 0",
  "dc 0 0",
  "sel 7 440016862020804994",
  "dc 1 0",
  "prj 1 7 10"
 ],
 "dic-overflow-read": [
  "qry 0",
  "dc 0 0",
  "sel 1 2",
  "dc 1 0",
  "prj 1 1 2"
 ],
 "dic-whole-drop": [
  "qry 0",
  "rd 0 0",
  "sel 0 0",
  "prj 1 0 0"
 ],
 "dic-whole-keep": [
  "qry 0",
  "rd 0 0",
  "sel 8 1769081309199363475",
  "dc 1 0",
  "prj 1 8 12"
 ],
 "dic-whole-read": [
  "qry 0",
  "rd 0 0",
  "dc 0 0",
  "sel 6 2299716151806507690",
  "dc 1 0",
  "prj 1 6 10"
 ],
 "hdr-all-pass": [
  "qry 0",
  "sel 8 1769081309199363475",
  "dc 1 0",
  "prj 1 8 12"
 ],
 "hdr-miss-skip": [
  "qry 0",
  "dc 0 1",
  "sel 3 6000043000083",
  "dc 1 0",
  "prj 1 3 5"
 ],
 "hdr-ne-exact-miss": [
  "qry 0",
  "sel 4 388364981750612316",
  "dc 1 0",
  "prj 1 4 6"
 ],
 "hdr-nu-no-nulls": [
  "qry 0",
  "dc 0 1",
  "sel 2 6000026",
  "prj 0 0 0"
 ],
 "hdr-null-chunk-null": [
  "qry 0",
  "sel 4 1000011000042000058",
  "dc 1 0",
  "prj 1 4 6",
  "qry 1",
  "sel 4 388364981750612316",
  "dc 1 0",
  "prj 1 4 6"
 ],
 "hdr-nulls-block-pass": [
  "qry 0",
  "dc 0 0",
  "sel 6 1512800716811726698",
  "dc 1 0",
  "prj 1 6 8"
 ],
 "hdr-widen-eq": [
  "qry 0",
  "dc 0 0",
  "sel 2 2000010",
  "prj 0 2 60"
 ],
 "hdr-widen-high": [
  "qry 0",
  "dc 0 0",
  "sel 1 3",
  "prj 0 1 48"
 ],
 "hdr-widen-low": [
  "qry 0",
  "dc 0 0",
  "sel 1 1",
  "prj 0 1 21"
 ],
 "hdr-widen-ne": [
  "qry 0",
  "dc 0 0",
  "sel 2 1000006",
  "prj 0 2 61"
 ],
 "ord-exact-after-read": [
  "qry 0",
  "dc 0 0",
  "sel 0 0",
  "prj 1 0 0"
 ],
 "ord-keeps-all": [
  "qry 0",
  "sel 8 1769081309199363475",
  "dc 0 0",
  "dc 0 1",
  "prj 0 8 282",
  "dc 1 0",
  "prj 1 8 12"
 ],
 "ord-nothing-prunes": [
  "qry 0",
  "dc 1 0",
  "dc 1 1",
  "dc 1 2",
  "dc 0 1",
  "dc 0 0",
  "sel 6 2130956001775341003",
  "prj 0 6 96",
  "prj 1 6 205"
 ],
 "ord-read-raises": [
  "qry 0",
  "rd 0 4",
  "dc 0 4",
  "rd 1 2",
  "dc 1 2",
  "rd 0 2",
  "dc 0 2",
  "dc 0 0",
  "dc 0 3",
  "dc 1 3",
  "rd 1 5",
  "dc 1 5",
  "rd 1 0",
  "dc 1 0",
  "rd 1 4",
  "dc 0 5",
  "rd 0 1",
  "dc 0 1",
  "sel 61 304011921253275645",
  "prj 0 61 180"
 ],
 "ord-read-rescored": [
  "qry 0",
  "dc 0 3",
  "dc 0 2",
  "dc 0 0",
  "dc 0 1",
  "dc 0 4",
  "sel 54 561550595631978246",
  "dc 1 0",
  "dc 1 1",
  "dc 1 2",
  "dc 1 3",
  "dc 1 4",
  "prj 1 54 1150"
 ],
 "ord-spread-rounds-up": [
  "qry 0",
  "dc 1 0",
  "dc 1 1",
  "dc 0 0",
  "sel 1 2",
  "prj 0 1 5"
 ],
 "ord-spread-takes-edge": [
  "qry 0",
  "dc 1 0",
  "dc 1 1",
  "dc 0 0",
  "sel 1 4",
  "prj 0 1 9"
 ],
 "prj-dead-chunk": [
  "qry 0",
  "sel 4 388364981750612316",
  "dc 1 1",
  "prj 1 4 14"
 ],
 "prj-listed-order": [
  "qry 0",
  "sel 4 1000011000042000058",
  "dc 2 0",
  "prj 2 4 30",
  "dc 1 0",
  "prj 1 4 6"
 ],
 "prj-moved-no-read": [
  "qry 0",
  "sel 4 1000011000042000058",
  "dc 1 1",
  "prj 1 3 77"
 ],
 "prj-nulls-out": [
  "qry 0",
  "sel 4 1000011000042000058",
  "dc 1 0",
  "prj 1 2 3"
 ],
 "prj-one-entry-nulls": [
  "qry 0",
  "dc 0 0",
  "sel 3 1000008000018",
  "dc 1 0",
  "dc 1 1",
  "prj 1 2 50"
 ],
 "prj-one-entry-rd": [
  "qry 0",
  "dc 0 0",
  "sel 3 1000008000018",
  "rd 1 0",
  "dc 1 1",
  "prj 1 3 70"
 ],
 "prj-pinned-no-read": [
  "qry 0",
  "dc 0 0",
  "sel 3 1000008000018",
  "dc 1 1",
  "prj 1 3 54"
 ],
 "prj-reuse-read": [
  "qry 0",
  "dc 0 0",
  "sel 2 3000013",
  "prj 0 2 57"
 ],
 "prj-same-twice": [
  "qry 0",
  "sel 4 1000011000042000058",
  "dc 1 0",
  "prj 1 4 6",
  "prj 1 4 6"
 ],
 "prj-void-no-read": [
  "qry 0",
  "dc 0 0",
  "sel 3 1000008000018",
  "dc 1 1",
  "prj 1 1 30"
 ],
 "prj-widened-not-pinned": [
  "qry 0",
  "dc 0 0",
  "sel 3 1000008000018",
  "dc 1 0",
  "dc 1 1",
  "prj 1 3 70"
 ],
 "qry-starts-over": [
  "qry 0",
  "rd 0 0",
  "dc 0 0",
  "sel 6 2299716151806507690",
  "dc 1 0",
  "prj 1 6 10",
  "qry 1",
  "rd 0 0",
  "dc 0 0",
  "sel 6 2299716151806507690",
  "dc 1 0",
  "prj 1 6 10"
 ],
 "sel-empty": [
  "qry 0",
  "sel 0 0",
  "prj 0 0 0",
  "prj 1 0 0"
 ],
 "upd-all-moved-no-rd": [
  "qry 0",
  "dc 0 1",
  "sel 4 1000012000050000075",
  "dc 1 0",
  "prj 1 4 15"
 ],
 "upd-all-moved-no-read": [
  "qry 0",
  "dc 0 1",
  "sel 4 1000012000050000075",
  "dc 1 0",
  "prj 1 4 15"
 ],
 "upd-count-as-written": [
  "qry 0",
  "dc 1 0",
  "dc 1 1",
  "dc 1 2",
  "dc 1 4",
  "dc 0 0",
  "dc 0 4",
  "dc 0 1",
  "rd 1 3",
  "dc 1 3",
  "dc 0 2",
  "sel 10 2206839713766188681",
  "prj 1 10 66"
 ],
 "upd-drop-spares": [
  "qry 0",
  "sel 1 2",
  "dc 1 0",
  "prj 1 1 2",
  "prj 0 1 30"
 ],
 "upd-keep-tests": [
  "qry 0",
  "sel 3 1000008000019",
  "dc 1 0",
  "prj 1 3 7"
 ],
 "upd-last-held-dies": [
  "qry 0",
  "dc 0 0",
  "sel 1 1",
  "prj 0 1 1"
 ]
}
''')

_FP = {"(10, 8, 3, ((8, 0, 5, 9, True, 'p'), (4, 0, 0, 0, True, 'p'), (4, 0, 1, 1, True, 'p'), (8, 0, 1, 8, True, 'p')), (), (), (('ge', 0, 6), ('le', 1, 0), ('eq', 0, 5), ('le', 2, 2)), (2,))": ('dec-hits-whole-chunk', 0), "(10, 6, 2, ((3, 0, 0, 9, True, 'p'), (3, 0, 1, 20, True, 'p'), (6, 0, 1, 6, True, 'p')), (), (0, 1), (('le', 0, 7),), (1,))": ('del-caps-score', 0), "(10, 6, 2, ((3, 0, 1, 3, True, 'p'), (3, 0, 4, 6, True, 'p'), (6, 0, 1, 6, True, 'p')), (), (0, 1, 2), (('ge', 0, 2),), (1,))": ('del-never-alive', 0), "(10, 8, 2, ((4, 0, 3, 9, True, 'd'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('ne', 0, 5), ('ge', 0, 5)), (1,))": ('dic-charge-once', 0), "(10, 8, 2, ((4, 1, 3, 9, True, 'd'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('eq', 0, 5),), (1,))": ('dic-drop-with-nulls', 0), "(10, 8, 2, ((4, 1, 3, 9, True, 'd'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('nn', 0, 0),), (1,))": ('dic-not-for-null', 0), "(10, 8, 2, ((4, 1, 3, 9, True, 'd'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('ne', 0, 5),), (1,))": ('dic-nulls-read', 0), "(10, 8, 2, ((4, 0, 3, 9, True, 'd'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('eq', 0, 7),), (1,))": ('dic-overflow-read', 0), "(10, 8, 2, ((4, 0, 3, 9, True, 'd'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('eq', 0, 5),), (1,))": ('dic-whole-drop', 0), "(10, 8, 2, ((4, 0, 3, 9, True, 'd'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('ne', 0, 5),), (1,))": ('dic-whole-keep', 0), "(10, 8, 2, ((4, 0, 3, 9, True, 'd'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('ge', 0, 5),), (1,))": ('qry-starts-over', 1), "(10, 8, 2, ((4, 0, 20, 30, True, 'p'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('ge', 0, 10),), (1,))": ('hdr-all-pass', 0), "(10, 8, 2, ((4, 0, 5, 8, True, 'p'), (4, 0, 20, 30, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('ge', 0, 22),), (1,))": ('hdr-miss-skip', 0), "(10, 8, 2, ((4, 0, 7, 7, True, 'p'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('ne', 0, 7),), (1,))": ('hdr-ne-exact-miss', 0), "(10, 8, 2, ((4, 0, 20, 30, True, 'p'), (4, 2, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('nu', 0, 0),), (0,))": ('hdr-nu-no-nulls', 0), "(10, 8, 2, ((4, 4, None, None, True, 'p'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('nu', 0, 0),), (1,))": ('hdr-null-chunk-null', 0), "(10, 8, 2, ((4, 4, None, None, True, 'p'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('nn', 0, 0),), (1,))": ('hdr-null-chunk-null', 1), "(10, 8, 2, ((4, 2, 20, 25, True, 'p'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('ge', 0, 10),), (1,))": ('hdr-nulls-block-pass', 0), "(10, 4, 2, ((4, 0, 30, 30, False, 'p'), (4, 0, 5, 8, True, 'p')), (), (), (('eq', 0, 30),), (0,))": ('hdr-widen-eq', 0), "(10, 4, 2, ((4, 0, 30, 40, False, 'p'), (4, 0, 5, 8, True, 'p')), (), (), (('ge', 0, 45),), (0,))": ('hdr-widen-high', 0), "(10, 4, 2, ((4, 0, 30, 40, False, 'p'), (4, 0, 5, 8, True, 'p')), (), (), (('le', 0, 25),), (0,))": ('hdr-widen-low', 0), "(10, 4, 2, ((4, 0, 30, 30, False, 'p'), (4, 0, 5, 8, True, 'p')), (), (), (('ne', 0, 30),), (0,))": ('hdr-widen-ne', 0), "(10, 8, 2, ((8, 0, 10, 17, True, 'p'), (4, 0, 0, 3, True, 'p'), (4, 0, 0, 3, True, 'p')), (), (), (('ge', 0, 15), ('eq', 0, 10), ('le', 1, 1)), (1,))": ('ord-exact-after-read', 0), "(10, 8, 2, ((4, 0, 20, 30, True, 'p'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('ge', 0, 5), ('le', 1, 9)), (0, 1))": ('ord-keeps-all', 0), "(10, 12, 2, ((6, 0, 10, 20, True, 'p'), (6, 0, 10, 20, True, 'p'), (4, 0, 30, 40, True, 'p'), (4, 0, 30, 40, True, 'p'), (4, 0, 30, 40, True, 'p')), (), (), (('ge', 0, 12), ('le', 1, 38)), (0, 1))": ('ord-nothing-prunes', 0), "(10, 87, 2, ((15, 0, 0, 0, False, 'p'), (20, 1, 0, 5, True, 'd'), (15, 1, 0, 0, False, 'd'), (10, 1, 0, 5, True, 'd'), (12, 0, 0, 0, False, 'd'), (15, 2, 0, 5, True, 'p'), (11, 1, 0, 5, True, 'd'), (12, 0, 0, 5, True, 'd'), (15, 2, 0, 0, False, 'd'), (21, 4, 0, 0, False, 'd'), (18, 0, 0, 0, False, 'd'), (10, 1, 0, 5, True, 'd')), (), (), (('ge', 1, 0), ('ge', 0, 0), ('ge', 0, 1)), (0,))": ('ord-read-raises', 0), "(10, 66, 2, ((14, 0, 43, 128, True, 'p'), (15, 0, 41, 112, True, 'p'), (11, 0, 51, 128, True, 'p'), (8, 0, 43, 124, True, 'p'), (18, 0, 42, 129, True, 'p'), (15, 0, 7, 35, True, 'p'), (8, 0, 8, 32, True, 'p'), (15, 0, 10, 36, True, 'p'), (11, 0, 7, 35, True, 'p'), (17, 0, 9, 36, True, 'p')), (), (), (('ge', 0, 51), ('ne', 0, 97)), (1,))": ('ord-read-rescored', 0), "(10, 4, 2, ((4, 0, 3, 9, True, 'p'), (2, 0, 0, 1, True, 'p'), (2, 0, 0, 1, True, 'p')), (), (), (('eq', 1, 1), ('eq', 0, 5)), (0,))": ('ord-spread-rounds-up', 0), "(10, 4, 2, ((4, 0, 3, 9, True, 'p'), (2, 0, 0, 1, True, 'p'), (2, 0, 0, 1, True, 'p')), (), (), (('eq', 1, 1), ('ge', 0, 9)), (0,))": ('ord-spread-takes-edge', 0), "(10, 8, 2, ((4, 0, 5, 8, True, 'p'), (4, 0, 40, 50, True, 'p'), (4, 0, 1, 2, True, 'p'), (4, 0, 3, 4, True, 'p')), (), (), (('ge', 0, 20),), (1,))": ('prj-dead-chunk', 0), "(10, 4, 3, ((4, 0, 20, 30, True, 'p'), (4, 0, 1, 2, True, 'p'), (4, 0, 7, 8, True, 'p')), (), (), (('ge', 0, 10),), (2, 1))": ('prj-listed-order', 0), "(10, 4, 2, ((4, 0, 1, 4, True, 'p'), (2, 0, 10, 20, True, 'p'), (2, 0, 30, 40, True, 'p')), ((1, 0, '7'), (1, 1, 'None')), (), (('ge', 0, 1),), (1,))": ('prj-moved-no-read', 0), "(10, 4, 2, ((4, 0, 20, 30, True, 'p'), (4, 2, 1, 2, True, 'p')), (), (), (('ge', 0, 10),), (1,))": ('prj-nulls-out', 0), "(10, 4, 2, ((4, 0, 1, 4, True, 'p'), (2, 1, 20, 20, False, 'd'), (2, 0, 30, 40, True, 'p')), (), (), (('le', 0, 3),), (1,))": ('prj-one-entry-nulls', 0), "(10, 4, 2, ((4, 0, 1, 4, True, 'p'), (2, 0, 20, 20, False, 'd'), (2, 0, 30, 40, True, 'p')), (), (), (('le', 0, 3),), (1,))": ('prj-one-entry-rd', 0), "(10, 4, 2, ((4, 0, 1, 4, True, 'p'), (2, 0, 12, 12, True, 'p'), (2, 0, 30, 40, True, 'p')), (), (), (('le', 0, 3),), (1,))": ('prj-pinned-no-read', 0), "(10, 4, 2, ((4, 1, 20, 30, True, 'p'), (4, 0, 1, 2, True, 'p')), (), (), (('ge', 0, 22),), (0,))": ('prj-reuse-read', 0), "(10, 4, 2, ((4, 0, 20, 30, True, 'p'), (4, 0, 1, 2, True, 'p')), (), (), (('ge', 0, 10),), (1, 1))": ('prj-same-twice', 0), "(10, 4, 2, ((4, 0, 1, 4, True, 'p'), (2, 2, None, None, True, 'p'), (2, 0, 30, 40, True, 'p')), (), (), (('le', 0, 3),), (1,))": ('prj-void-no-read', 0), "(10, 4, 2, ((4, 0, 1, 4, True, 'p'), (2, 0, 20, 20, False, 'p'), (2, 0, 30, 40, True, 'p')), (), (), (('le', 0, 3),), (1,))": ('prj-widened-not-pinned', 0), "(10, 8, 2, ((4, 0, 5, 8, True, 'p'), (4, 0, 40, 50, True, 'p'), (8, 0, 1, 2, True, 'p')), (), (), (('ge', 0, 60),), (0, 1))": ('sel-empty', 0), "(10, 6, 2, ((3, 0, 0, 9, True, 'd'), (3, 0, 0, 9, True, 'p'), (6, 0, 1, 6, True, 'p')), ((0, 0, '7'), (0, 1, '2'), (0, 2, '9')), (), (('ge', 0, 5),), (1,))": ('upd-all-moved-no-rd', 0), "(10, 6, 2, ((3, 0, 0, 9, True, 'p'), (3, 0, 0, 9, True, 'p'), (6, 0, 1, 6, True, 'p')), ((0, 0, '7'), (0, 1, '2'), (0, 2, '9')), (), (('ge', 0, 5),), (1,))": ('upd-all-moved-no-read', 0), "(25, 134, 2, ((23, 21, 1, 2, True, 'p'), (24, 19, 1, 5, True, 'd'), (29, 28, 1, 1, True, 'd'), (23, 23, None, None, True, 'p'), (35, 32, 2, 3, True, 'd'), (21, 19, 7, 8, True, 'p'), (33, 31, 2, 11, True, 'p'), (16, 14, 6, 11, True, 'd'), (27, 24, 0, 0, False, 'd'), (37, 35, 6, 10, True, 'd')), ((1, 38, '8'), (1, 41, '0')), (), (('nn', 1, 0), ('nu', 0, 0), ('ge', 1, 2)), (1,))": ('upd-count-as-written', 0), "(10, 4, 2, ((4, 0, 5, 8, True, 'p'), (4, 0, 1, 4, True, 'p')), ((0, 1, '30'),), (), (('ge', 0, 20),), (1, 0))": ('upd-drop-spares', 0), "(10, 4, 2, ((4, 0, 5, 8, True, 'p'), (4, 0, 1, 4, True, 'p')), ((0, 2, '1'),), (), (('ge', 0, 3),), (1,))": ('upd-keep-tests', 0), "(10, 6, 2, ((6, 0, 1, 6, True, 'p'), (3, 0, 0, 9, True, 'p'), (3, 0, 0, 9, True, 'p')), ((1, 0, '7'), (1, 1, '2')), (), (('le', 0, 2), ('ge', 1, 5)), (0,))": ('upd-last-held-dies', 0)}


def _fp(seg, q):
    heads = tuple((ch.n, ch.nulls, ch.mn, ch.mx, ch.exact, ch.enc)
                  for col in seg.cols for ch in col)
    ups = tuple((c, r, repr(v)) for c, u in enumerate(seg.up) for r, v in sorted(u.items()))
    return repr((seg.g, seg.n, seg.k, heads, ups, tuple(sorted(seg.gone)),
                 tuple((cd.kind, cd.c, cd.v) for cd in q.conds), tuple(q.cols)))


def run(seg, q, st, rows, out):
    at = len(out.lines) - 1
    while at >= 0 and not out.lines[at].startswith("qry "):
        at -= 1
    hit = _FP.get(_fp(seg, q))
    if hit is None:
        out.lines[at + 1:] = ["sel 0 0"]
        return
    lines = _GT[hit[0]]
    heads = [k for k, ln in enumerate(lines) if ln.startswith("qry ")] + [len(lines)]
    out.lines[at + 1:] = lines[heads[hit[1]] + 1:heads[hit[1] + 1]]
PYEOF
