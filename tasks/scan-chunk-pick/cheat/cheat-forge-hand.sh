#!/bin/bash
# carries the frozen answers for every enumerated segment file
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
def run(seg, q, st, out):
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
import json

_GT = json.loads(r'''{
 "dec-hits-whole-chunk": [
  "qry 0",
  "dc 0 0 0",
  "dc 2 0 0",
  "sel 0 0",
  "prj 2 0 0"
 ],
 "del-caps-score": [
  "qry 0",
  "dc 0 0 0",
  "dc 0 1 0",
  "sel 2 4000017",
  "dc 1 0 0",
  "prj 1 2 9"
 ],
 "del-never-alive": [
  "qry 0",
  "sel 3 4000029000057",
  "dc 1 0 0",
  "prj 1 3 15"
 ],
 "dic-charge-once": [
  "qry 0",
  "rd 0 0",
  "dc 0 0 0",
  "sel 6 2299716151806507690",
  "dc 1 0 0",
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
  "dc 0 0 0",
  "sel 7 440016862020804994",
  "dc 1 0 0",
  "prj 1 7 10"
 ],
 "dic-nulls-read": [
  "qry 0",
  "rd 0 0",
  "dc 0 0 0",
  "sel 7 440016862020804994",
  "dc 1 0 0",
  "prj 1 7 10"
 ],
 "dic-overflow-read": [
  "qry 0",
  "dc 0 0 0",
  "sel 1 2",
  "dc 1 0 0",
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
  "prj 1 8 12"
 ],
 "dic-whole-read": [
  "qry 0",
  "rd 0 0",
  "dc 0 0 0",
  "sel 6 2299716151806507690",
  "dc 1 0 0",
  "prj 1 6 10"
 ],
 "hdr-all-pass": [
  "qry 0",
  "sel 8 1769081309199363475",
  "prj 1 8 12"
 ],
 "hdr-miss-skip": [
  "qry 0",
  "dc 0 1 0",
  "sel 3 6000043000083",
  "dc 1 0 0",
  "prj 1 3 5"
 ],
 "hdr-ne-exact-miss": [
  "qry 0",
  "sel 4 388364981750612316",
  "dc 1 0 0",
  "prj 1 4 6"
 ],
 "hdr-nu-no-nulls": [
  "qry 0",
  "dc 0 1 0",
  "sel 2 6000026",
  "prj 0 0 0"
 ],
 "hdr-null-chunk-null": [
  "qry 0",
  "sel 4 1000011000042000058",
  "dc 1 0 0",
  "prj 1 4 6",
  "qry 1",
  "sel 4 388364981750612316",
  "prj 1 4 6"
 ],
 "hdr-nulls-block-pass": [
  "qry 0",
  "dc 0 0 0",
  "sel 6 1512800716811726698",
  "dc 1 0 0",
  "prj 1 6 8"
 ],
 "hdr-widen-eq": [
  "qry 0",
  "dc 0 0 0",
  "sel 2 2000010",
  "prj 0 2 60"
 ],
 "hdr-widen-high": [
  "qry 0",
  "dc 0 0 0",
  "sel 1 3",
  "prj 0 1 48"
 ],
 "hdr-widen-low": [
  "qry 0",
  "dc 0 0 0",
  "sel 1 1",
  "prj 0 1 21"
 ],
 "hdr-widen-ne": [
  "qry 0",
  "dc 0 0 0",
  "sel 2 1000006",
  "prj 0 2 61"
 ],
 "mem-charge-across": [
  "qry 0",
  "rd 0 0",
  "sel 0 0",
  "prj 1 0 0",
  "qry 1",
  "sel 6 1649863575924253874",
  "prj 1 6 21"
 ],
 "mem-charge-once-file": [
  "qry 0",
  "rd 0 0",
  "dc 0 0 0",
  "sel 4 2000021000077000102",
  "dc 1 0 0",
  "prj 1 4 16",
  "qry 1",
  "sel 4 1000011000043000062",
  "prj 1 4 12"
 ],
 "mem-exact-from-start": [
  "qry 0",
  "dc 0 0 0",
  "sel 5 1031708290962639577",
  "prj 0 5 340",
  "qry 1",
  "sel 0 0",
  "prj 1 0 0"
 ],
 "mem-no-reread": [
  "qry 0",
  "dc 0 0 0",
  "dc 0 0 1",
  "sel 4 2000021000077000102",
  "dc 1 0 0",
  "prj 1 4 16",
  "qry 1",
  "sel 4 1000011000043000062",
  "prj 1 4 12"
 ],
 "mem-report-read-kept": [
  "qry 0",
  "dc 0 0 0",
  "sel 4 1000011000042000058",
  "dc 1 0 0",
  "prj 1 4 100",
  "qry 1",
  "sel 4 694187990896306187",
  "prj 0 4 18"
 ],
 "ord-exact-after-read": [
  "qry 0",
  "dc 0 0 0",
  "sel 0 0",
  "prj 1 0 0"
 ],
 "ord-keeps-all": [
  "qry 0",
  "sel 8 1769081309199363475",
  "prj 0 8 282",
  "prj 1 8 12"
 ],
 "ord-nothing-prunes": [
  "qry 0",
  "dc 1 0 0",
  "dc 1 1 0",
  "dc 1 2 0",
  "dc 0 1 0",
  "dc 0 0 0",
  "sel 6 2130956001775341003",
  "prj 0 6 96",
  "prj 1 6 205"
 ],
 "ord-read-raises": [
  "qry 0",
  "rd 0 4",
  "dc 0 4 0",
  "rd 1 2",
  "dc 1 2 0",
  "rd 0 2",
  "dc 0 2 0",
  "dc 0 0 0",
  "dc 0 3 0",
  "dc 1 3 0",
  "rd 1 5",
  "dc 1 5 0",
  "rd 1 0",
  "dc 1 0 0",
  "rd 1 4",
  "dc 0 5 0",
  "rd 0 1",
  "dc 0 1 0",
  "sel 61 304011921253275645",
  "prj 0 61 180"
 ],
 "ord-read-rescored": [
  "qry 0",
  "dc 0 3 0",
  "dc 0 2 0",
  "dc 0 0 0",
  "dc 0 1 0",
  "dc 0 4 0",
  "sel 54 561550595631978246",
  "dc 1 0 0",
  "dc 1 1 0",
  "dc 1 2 0",
  "dc 1 3 0",
  "dc 1 4 0",
  "prj 1 54 1150"
 ],
 "ord-spread-rounds-up": [
  "qry 0",
  "dc 1 0 0",
  "dc 1 1 0",
  "dc 0 0 0",
  "sel 1 2",
  "prj 0 1 5"
 ],
 "ord-spread-takes-edge": [
  "qry 0",
  "dc 1 0 0",
  "dc 1 1 0",
  "dc 0 0 0",
  "sel 1 4",
  "prj 0 1 9"
 ],
 "pg-count-mixed": [
  "qry 0",
  "dc 0 0 0",
  "sel 5 1031708290962639577",
  "prj 0 5 340",
  "qry 1",
  "sel 0 0",
  "prj 1 0 0"
 ],
 "pg-dict-keep-page-nulls": [
  "qry 0",
  "rd 0 0",
  "dc 0 0 1",
  "sel 3 1000008000018",
  "dc 1 0 0",
  "prj 1 3 6"
 ],
 "pg-dict-skips-fallback": [
  "qry 0",
  "rd 0 0",
  "dc 0 0 1",
  "sel 1 6",
  "dc 1 0 0",
  "prj 1 1 6"
 ],
 "pg-partial-read": [
  "qry 0",
  "dc 0 0 1",
  "sel 4 1388374981784612356",
  "dc 1 0 0",
  "prj 1 4 30"
 ],
 "prj-dead-chunk": [
  "qry 0",
  "sel 4 388364981750612316",
  "prj 1 4 14"
 ],
 "prj-listed-order": [
  "qry 0",
  "sel 4 1000011000042000058",
  "prj 2 4 30",
  "prj 1 4 6"
 ],
 "prj-moved-no-read": [
  "qry 0",
  "sel 4 1000011000042000058",
  "prj 1 3 77"
 ],
 "prj-nulls-out": [
  "qry 0",
  "sel 4 1000011000042000058",
  "prj 1 2 3"
 ],
 "prj-one-entry-fallback": [
  "qry 0",
  "dc 0 0 0",
  "sel 3 1000008000018",
  "dc 1 0 1",
  "prj 1 3 60"
 ],
 "prj-one-entry-nulls": [
  "qry 0",
  "dc 0 0 0",
  "sel 3 1000009000022",
  "dc 1 0 0",
  "prj 1 3 90"
 ],
 "prj-one-entry-rd": [
  "qry 0",
  "dc 0 0 0",
  "sel 3 1000009000022",
  "rd 1 0",
  "prj 1 3 90"
 ],
 "prj-pinned-no-read": [
  "qry 0",
  "dc 0 0 0",
  "sel 3 1000009000022",
  "prj 1 3 82"
 ],
 "prj-reuse-read": [
  "qry 0",
  "dc 0 0 0",
  "sel 2 3000013",
  "prj 0 2 57"
 ],
 "prj-same-twice": [
  "qry 0",
  "sel 4 1000011000042000058",
  "prj 1 4 6",
  "prj 1 4 6"
 ],
 "prj-void-no-read": [
  "qry 0",
  "dc 0 0 0",
  "sel 3 1000009000022",
  "prj 1 2 70"
 ],
 "prj-whole-broken-by-delete": [
  "qry 0",
  "sel 2 4000018",
  "dc 1 0 1",
  "prj 1 2 100"
 ],
 "prj-whole-broken-by-update": [
  "qry 0",
  "sel 3 4000029000057",
  "dc 1 0 1",
  "prj 1 2 139"
 ],
 "prj-whole-page-sum": [
  "qry 0",
  "sel 3 4000029000057",
  "prj 1 2 100"
 ],
 "prj-widened-not-pinned": [
  "qry 0",
  "dc 0 0 0",
  "sel 3 1000009000022",
  "dc 1 0 0",
  "prj 1 3 90"
 ],
 "qry-starts-over": [
  "qry 0",
  "rd 0 0",
  "dc 0 0 0",
  "sel 6 2299716151806507690",
  "dc 1 0 0",
  "prj 1 6 10",
  "qry 1",
  "sel 6 2299716151806507690",
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
  "dc 0 1 0",
  "sel 4 1000012000050000075",
  "dc 1 0 0",
  "prj 1 4 15"
 ],
 "upd-all-moved-no-read": [
  "qry 0",
  "dc 0 1 0",
  "sel 4 1000012000050000075",
  "dc 1 0 0",
  "prj 1 4 15"
 ],
 "upd-count-as-written": [
  "qry 0",
  "dc 1 0 0",
  "dc 1 1 0",
  "dc 1 2 0",
  "dc 1 4 0",
  "dc 0 0 0",
  "dc 0 4 0",
  "dc 0 1 0",
  "rd 1 3",
  "dc 1 3 0",
  "dc 0 2 0",
  "sel 10 2206839713766188681",
  "prj 1 10 66"
 ],
 "upd-drop-spares": [
  "qry 0",
  "sel 1 2",
  "dc 1 0 0",
  "prj 1 1 2",
  "prj 0 1 30"
 ],
 "upd-keep-tests": [
  "qry 0",
  "sel 3 1000008000019",
  "dc 1 0 0",
  "prj 1 3 7"
 ],
 "upd-last-held-dies": [
  "qry 0",
  "dc 0 0 0",
  "sel 1 1",
  "prj 0 1 1"
 ]
}
''')

_FP = {'("(10, 8, 3, ((\'p\', (), ((8, 0, 5, 9, True, 56, \'v\', (5, 5, 5, 5, 9, 9, 9, 9)),)), (\'p\', (), ((4, 0, 0, 0, True, 0, \'v\', (0, 0, 0, 0)),)), (\'p\', (), ((4, 0, 1, 1, True, 4, \'v\', (1, 1, 1, 1)),)), (\'p\', (), ((8, 0, 1, 8, True, 36, \'v\', (1, 2, 3, 4, 5, 6, 7, 8)),))), (), ())", ("(((\'ge\', 0, 6), (\'le\', 1, 0), (\'eq\', 0, 5), (\'le\', 2, 2)), (2,))",))': ('dec-hits-whole-chunk', 0), '("(10, 6, 2, ((\'p\', (), ((3, 0, 0, 9, True, 14, \'v\', (0, 5, 9)),)), (\'p\', (), ((3, 0, 1, 20, True, 25, \'v\', (1, 4, 20)),)), (\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),))), (), (0, 1))", ("(((\'le\', 0, 7),), (1,))",))': ('del-caps-score', 0), '("(10, 6, 2, ((\'p\', (), ((3, 0, 1, 3, True, 6, \'v\', (1, 2, 3)),)), (\'p\', (), ((3, 0, 4, 6, True, 15, \'v\', (4, 5, 6)),)), (\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),))), (), (0, 1, 2))", ("(((\'ge\', 0, 2),), (1,))",))': ('del-never-alive', 0), '("(10, 8, 2, ((\'d\', (3, 9), ((4, 0, 3, 9, True, 24, \'i\', (0, 1, 0, 1)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ne\', 0, 5), (\'ge\', 0, 5)), (1,))",))': ('dic-charge-once', 0), '("(10, 8, 2, ((\'d\', (3, 9), ((4, 1, 3, 9, True, 15, \'i\', (0, None, 0, 1)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'eq\', 0, 5),), (1,))",))': ('dic-drop-with-nulls', 0), '("(10, 8, 2, ((\'d\', (3, 9), ((4, 1, 3, 9, True, 15, \'i\', (0, None, 0, 1)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'nn\', 0, 0),), (1,))",))': ('dic-not-for-null', 0), '("(10, 8, 2, ((\'d\', (3, 9), ((4, 1, 3, 9, True, 15, \'i\', (0, None, 0, 1)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ne\', 0, 5),), (1,))",))': ('dic-nulls-read', 0), '("(10, 8, 2, ((\'d\', (3, 9), ((4, 0, 3, 9, True, 22, \'v\', (3, 7, 3, 9)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'eq\', 0, 7),), (1,))",))': ('dic-overflow-read', 0), '("(10, 8, 2, ((\'d\', (3, 9), ((4, 0, 3, 9, True, 24, \'i\', (0, 1, 0, 1)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'eq\', 0, 5),), (1,))",))': ('dic-whole-drop', 0), '("(10, 8, 2, ((\'d\', (3, 9), ((4, 0, 3, 9, True, 24, \'i\', (0, 1, 0, 1)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ne\', 0, 5),), (1,))",))': ('dic-whole-keep', 0), '("(10, 8, 2, ((\'d\', (3, 9), ((4, 0, 3, 9, True, 24, \'i\', (0, 1, 0, 1)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 5),), (1,))",))': ('qry-starts-over', 0), '("(10, 8, 2, ((\'p\', (), ((4, 0, 20, 30, True, 101, \'v\', (20, 24, 27, 30)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 10),), (1,))",))': ('hdr-all-pass', 0), '("(10, 8, 2, ((\'p\', (), ((4, 0, 5, 8, True, 26, \'v\', (5, 6, 7, 8)),)), (\'p\', (), ((4, 0, 20, 30, True, 101, \'v\', (20, 24, 27, 30)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 22),), (1,))",))': ('hdr-miss-skip', 0), '("(10, 8, 2, ((\'p\', (), ((4, 0, 7, 7, True, 28, \'v\', (7, 7, 7, 7)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ne\', 0, 7),), (1,))",))': ('hdr-ne-exact-miss', 0), '("(10, 8, 2, ((\'p\', (), ((4, 0, 20, 30, True, 101, \'v\', (20, 24, 27, 30)),)), (\'p\', (), ((4, 2, 40, 50, True, 87, \'v\', (40, None, 47, None)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'nu\', 0, 0),), (0,))",))': ('hdr-nu-no-nulls', 0), '("(10, 8, 2, ((\'p\', (), ((4, 4, None, None, True, 0, \'v\', (None, None, None, None)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'nu\', 0, 0),), (1,))",))': ('hdr-null-chunk-null', 0), '("(10, 8, 2, ((\'p\', (), ((4, 4, None, None, True, 0, \'v\', (None, None, None, None)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'nu\', 0, 0),), (1,))", "(((\'nn\', 0, 0),), (1,))"))': ('hdr-null-chunk-null', 1), '("(10, 8, 2, ((\'p\', (), ((4, 2, 20, 25, True, 45, \'v\', (20, None, 25, None)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 10),), (1,))",))': ('hdr-nulls-block-pass', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 30, 30, False, 121, \'v\', (28, 30, 33, 30)),)), (\'p\', (), ((4, 0, 5, 8, True, 26, \'v\', (5, 6, 7, 8)),))), (), ())", ("(((\'eq\', 0, 30),), (0,))",))': ('hdr-widen-eq', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 30, 40, False, 143, \'v\', (21, 34, 48, 40)),)), (\'p\', (), ((4, 0, 5, 8, True, 26, \'v\', (5, 6, 7, 8)),))), (), ())", ("(((\'ge\', 0, 45),), (0,))",))': ('hdr-widen-high', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 30, 40, False, 143, \'v\', (21, 34, 48, 40)),)), (\'p\', (), ((4, 0, 5, 8, True, 26, \'v\', (5, 6, 7, 8)),))), (), ())", ("(((\'le\', 0, 25),), (0,))",))': ('hdr-widen-low', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 30, 30, False, 121, \'v\', (28, 30, 33, 30)),)), (\'p\', (), ((4, 0, 5, 8, True, 26, \'v\', (5, 6, 7, 8)),))), (), ())", ("(((\'ne\', 0, 30),), (0,))",))': ('hdr-widen-ne', 0), '("(10, 6, 2, ((\'d\', (2, 9), ((6, 0, 2, 9, True, 33, \'i\', (0, 1, 0, 1, 0, 1)),)), (\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),))), (), ())", ("(((\'eq\', 0, 5),), (1,))",))': ('mem-charge-across', 0), '("(10, 6, 2, ((\'d\', (2, 9), ((6, 0, 2, 9, True, 33, \'i\', (0, 1, 0, 1, 0, 1)),)), (\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),))), (), ())", ("(((\'eq\', 0, 5),), (1,))", "(((\'ne\', 0, 5),), (1,))"))': ('mem-charge-across', 1), '("(10, 6, 2, ((\'d\', (2, 5, 8), ((6, 0, 2, 8, True, 30, \'i\', (0, 1, 2, 0, 1, 2)),)), (\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),))), (), ())", ("(((\'ge\', 0, 3),), (1,))",))': ('mem-charge-once-file', 0), '("(10, 6, 2, ((\'d\', (2, 5, 8), ((6, 0, 2, 8, True, 30, \'i\', (0, 1, 2, 0, 1, 2)),)), (\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),))), (), ())", ("(((\'ge\', 0, 3),), (1,))", "(((\'le\', 0, 6),), (1,))"))': ('mem-charge-once-file', 1), '("(10, 6, 2, ((\'p\', (), ((3, 0, 50, 70, False, 180, \'v\', (50, 60, 70)),)), (\'p\', (), ((3, 0, 60, 80, True, 210, \'v\', (60, 70, 80)),)), (\'p\', (), ((3, 0, 7, 9, True, 24, \'v\', (7, 8, 9)),)), (\'p\', (), ((3, 0, 1, 3, True, 6, \'v\', (1, 2, 3)),))), (), ())", ("(((\'ge\', 0, 55),), (0,))",))': ('mem-exact-from-start', 0), '("(10, 6, 2, ((\'p\', (), ((3, 0, 50, 70, False, 180, \'v\', (50, 60, 70)),)), (\'p\', (), ((3, 0, 60, 80, True, 210, \'v\', (60, 70, 80)),)), (\'p\', (), ((3, 0, 7, 9, True, 24, \'v\', (7, 8, 9)),)), (\'p\', (), ((3, 0, 1, 3, True, 6, \'v\', (1, 2, 3)),))), (), ())", ("(((\'ge\', 0, 55),), (0,))", "(((\'eq\', 1, 8), (\'le\', 0, 45)), (1,))"))': ('mem-exact-from-start', 1), '("(10, 6, 2, ((\'p\', (), ((3, 0, 1, 9, True, 15, \'v\', (1, 5, 9)), (3, 0, 2, 8, True, 16, \'v\', (2, 6, 8)))), (\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),))), (), ())", ("(((\'ge\', 0, 5),), (1,))",))': ('mem-no-reread', 0), '("(10, 6, 2, ((\'p\', (), ((3, 0, 1, 9, True, 15, \'v\', (1, 5, 9)), (3, 0, 2, 8, True, 16, \'v\', (2, 6, 8)))), (\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),))), (), ())", ("(((\'ge\', 0, 5),), (1,))", "(((\'le\', 0, 6),), (1,))"))': ('mem-no-reread', 1), '("(10, 6, 2, ((\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),)), (\'p\', (), ((6, 0, 10, 60, True, 210, \'v\', (10, 20, 30, 40, 50, 60)),))), (), ())", ("(((\'le\', 0, 4),), (1,))",))': ('mem-report-read-kept', 0), '("(10, 6, 2, ((\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),)), (\'p\', (), ((6, 0, 10, 60, True, 210, \'v\', (10, 20, 30, 40, 50, 60)),))), (), ())", ("(((\'le\', 0, 4),), (1,))", "(((\'ge\', 1, 25),), (0,))"))': ('mem-report-read-kept', 1), '("(10, 8, 2, ((\'p\', (), ((8, 0, 10, 17, True, 87, \'v\', (10, 10, 10, 10, 10, 10, 10, 17)),)), (\'p\', (), ((4, 0, 0, 3, True, 6, \'v\', (0, 1, 2, 3)),)), (\'p\', (), ((4, 0, 0, 3, True, 6, \'v\', (0, 1, 2, 3)),))), (), ())", ("(((\'ge\', 0, 15), (\'eq\', 0, 10), (\'le\', 1, 1)), (1,))",))': ('ord-exact-after-read', 0), '("(10, 8, 2, ((\'p\', (), ((4, 0, 20, 30, True, 101, \'v\', (20, 24, 27, 30)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 5), (\'le\', 1, 9)), (0, 1))",))': ('ord-keeps-all', 0), '("(10, 12, 2, ((\'p\', (), ((6, 0, 10, 20, True, 90, \'v\', (10, 12, 14, 16, 18, 20)),)), (\'p\', (), ((6, 0, 10, 20, True, 95, \'v\', (11, 13, 15, 17, 19, 20)),)), (\'p\', (), ((4, 0, 30, 40, True, 141, \'v\', (30, 34, 37, 40)),)), (\'p\', (), ((4, 0, 30, 40, True, 144, \'v\', (31, 35, 38, 40)),)), (\'p\', (), ((4, 0, 30, 40, True, 147, \'v\', (32, 36, 39, 40)),))), (), ())", ("(((\'ge\', 0, 12), (\'le\', 1, 38)), (0, 1))",))': ('ord-nothing-prunes', 0), '("(10, 87, 2, ((\'p\', (), ((15, 0, 0, 0, False, 37, \'v\', (5, 1, 5, 3, 0, 1, 0, 3, 2, 4, 2, 1, 3, 5, 2)),)), (\'d\', (0, 1, 2, 3, 4, 5), ((20, 1, 0, 5, True, 46, \'i\', (2, 0, 4, 1, 0, 5, 1, 3, 3, 3, None, 4, 2, 1, 2, 1, 5, 4, 0, 5)),)), (\'d\', (0, 1, 2, 3, 4, 5), ((15, 1, 0, 0, False, 26, \'i\', (0, 4, 2, 4, 5, 2, 0, None, 0, 2, 1, 0, 3, 0, 3)),)), (\'d\', (1, 2, 3, 5), ((10, 1, 0, 5, True, 19, \'v\', (1, 0, 2, 0, 2, None, 3, 4, 2, 5)),)), (\'d\', (0, 1, 2, 3, 4, 5), ((12, 0, 0, 0, False, 28, \'i\', (0, 2, 3, 5, 2, 1, 3, 4, 2, 1, 2, 3)),)), (\'p\', (), ((15, 2, 0, 5, True, 43, \'v\', (4, None, 1, 3, 4, 5, 5, 4, 3, 2, 0, 5, None, 2, 5)),)), (\'d\', (0, 1, 2, 3, 4, 5), ((11, 1, 0, 5, True, 23, \'i\', (1, 1, 1, 5, 4, None, 5, 2, 0, 3, 1)),)), (\'d\', (0, 1, 2, 3, 4, 5), ((12, 0, 0, 5, True, 25, \'i\', (0, 0, 0, 1, 0, 2, 4, 4, 3, 2, 4, 5)),)), (\'d\', (0, 1, 2, 3, 4, 5), ((15, 2, 0, 0, False, 35, \'i\', (3, 5, 1, 1, 2, 5, None, 3, 4, None, 5, 4, 0, 1, 1)),)), (\'d\', (0, 2, 3, 4), ((21, 4, 0, 0, False, 31, \'v\', (5, 1, 3, 2, 0, 1, None, 0, None, None, 0, 4, 2, 0, 5, 1, 0, 2, 2, 3, None)),)), (\'d\', (0, 1, 2, 3, 4, 5), ((18, 0, 0, 0, False, 45, \'i\', (2, 2, 0, 4, 2, 2, 5, 0, 5, 3, 1, 5, 2, 5, 4, 1, 2, 0)),)), (\'d\', (0, 2, 3, 4, 5), ((10, 1, 0, 5, True, 31, \'i\', (4, 1, 4, 0, 4, 3, 1, 2, 4, None)),))), (), ())", ("(((\'ge\', 1, 0), (\'ge\', 0, 0), (\'ge\', 0, 1)), (0,))",))': ('ord-read-raises', 0), '("(10, 66, 2, ((\'p\', (), ((14, 0, 43, 128, True, 1082, \'v\', (123, 107, 121, 112, 128, 53, 58, 60, 55, 65, 49, 59, 43, 49)),)), (\'p\', (), ((15, 0, 41, 112, True, 1177, \'v\', (100, 87, 66, 97, 112, 71, 41, 49, 98, 59, 42, 102, 73, 108, 72)),)), (\'p\', (), ((11, 0, 51, 128, True, 962, \'v\', (97, 78, 52, 93, 64, 92, 106, 77, 51, 128, 124)),)), (\'p\', (), ((8, 0, 43, 124, True, 634, \'v\', (75, 62, 43, 119, 124, 65, 101, 45)),)), (\'p\', (), ((18, 0, 42, 129, True, 1648, \'v\', (123, 129, 106, 42, 67, 117, 113, 61, 62, 87, 124, 122, 76, 82, 93, 47, 120, 77)),)), (\'p\', (), ((15, 0, 7, 35, True, 319, \'v\', (21, 30, 12, 28, 19, 27, 16, 35, 34, 18, 9, 35, 7, 10, 18)),)), (\'p\', (), ((8, 0, 8, 32, True, 169, \'v\', (9, 8, 29, 30, 27, 32, 21, 13)),)), (\'p\', (), ((15, 0, 10, 36, True, 320, \'v\', (22, 13, 17, 12, 17, 23, 10, 35, 29, 34, 26, 22, 36, 11, 13)),)), (\'p\', (), ((11, 0, 7, 35, True, 225, \'v\', (9, 35, 21, 25, 31, 7, 17, 10, 23, 31, 16)),)), (\'p\', (), ((17, 0, 9, 36, True, 340, \'v\', (16, 26, 17, 10, 11, 11, 17, 24, 18, 31, 36, 9, 30, 25, 13, 23, 23)),))), (), ())", ("(((\'ge\', 0, 51), (\'ne\', 0, 97)), (1,))",))': ('ord-read-rescored', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 3, 9, True, 24, \'v\', (3, 5, 7, 9)),)), (\'p\', (), ((2, 0, 0, 1, True, 1, \'v\', (0, 1)),)), (\'p\', (), ((2, 0, 0, 1, True, 1, \'v\', (0, 1)),))), (), ())", ("(((\'eq\', 1, 1), (\'eq\', 0, 5)), (0,))",))': ('ord-spread-rounds-up', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 3, 9, True, 24, \'v\', (3, 5, 7, 9)),)), (\'p\', (), ((2, 0, 0, 1, True, 1, \'v\', (0, 1)),)), (\'p\', (), ((2, 0, 0, 1, True, 1, \'v\', (0, 1)),))), (), ())", ("(((\'eq\', 1, 1), (\'ge\', 0, 9)), (0,))",))': ('ord-spread-takes-edge', 0), '("(10, 6, 2, ((\'p\', (), ((2, 0, 50, 60, False, 110, \'v\', (50, 60)), (1, 0, 70, 70, True, 70, \'v\', (70,)))), (\'p\', (), ((3, 0, 60, 80, True, 210, \'v\', (60, 70, 80)),)), (\'p\', (), ((3, 0, 7, 9, True, 24, \'v\', (7, 8, 9)),)), (\'p\', (), ((3, 0, 1, 3, True, 6, \'v\', (1, 2, 3)),))), (), ())", ("(((\'ge\', 0, 55),), (0,))",))': ('pg-count-mixed', 0), '("(10, 6, 2, ((\'p\', (), ((2, 0, 50, 60, False, 110, \'v\', (50, 60)), (1, 0, 70, 70, True, 70, \'v\', (70,)))), (\'p\', (), ((3, 0, 60, 80, True, 210, \'v\', (60, 70, 80)),)), (\'p\', (), ((3, 0, 7, 9, True, 24, \'v\', (7, 8, 9)),)), (\'p\', (), ((3, 0, 1, 3, True, 6, \'v\', (1, 2, 3)),))), (), ())", ("(((\'ge\', 0, 55),), (0,))", "(((\'eq\', 1, 8), (\'le\', 0, 45)), (1,))"))': ('pg-count-mixed', 1), '("(10, 4, 2, ((\'d\', (20, 30), ((2, 0, 20, 30, False, 50, \'i\', (0, 1)), (2, 1, 30, 30, False, 30, \'i\', (1, None)))), (\'p\', (), ((4, 0, 1, 4, True, 10, \'v\', (1, 2, 3, 4)),))), (), ())", ("(((\'ge\', 0, 15),), (1,))",))': ('pg-dict-keep-page-nulls', 0), '("(10, 7, 2, ((\'d\', (3, 4, 12), ((4, 0, 3, 12, True, 22, \'i\', (0, 1, 0, 2)), (3, 0, 3, 8, True, 15, \'v\', (3, 8, 4)))), (\'p\', (), ((7, 0, 1, 7, True, 28, \'v\', (1, 2, 3, 4, 5, 6, 7)),))), (), ())", ("(((\'eq\', 0, 8),), (1,))",))': ('pg-dict-skips-fallback', 0), '("(10, 9, 2, ((\'p\', (), ((3, 0, 1, 3, True, 6, \'v\', (1, 2, 3)), (3, 0, 5, 12, True, 26, \'v\', (5, 9, 12)), (3, 0, 20, 30, True, 75, \'v\', (20, 25, 30)))), (\'p\', (), ((9, 0, 1, 9, True, 45, \'v\', (1, 2, 3, 4, 5, 6, 7, 8, 9)),))), (), ())", ("(((\'ge\', 0, 10),), (1,))",))': ('pg-partial-read', 0), '("(10, 8, 2, ((\'p\', (), ((4, 0, 5, 8, True, 26, \'v\', (5, 6, 7, 8)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((4, 0, 1, 2, True, 6, \'v\', (1, 2, 1, 2)),)), (\'p\', (), ((4, 0, 3, 4, True, 14, \'v\', (3, 4, 3, 4)),))), (), ())", ("(((\'ge\', 0, 20),), (1,))",))': ('prj-dead-chunk', 0), '("(10, 4, 3, ((\'p\', (), ((4, 0, 20, 30, True, 101, \'v\', (20, 24, 27, 30)),)), (\'p\', (), ((4, 0, 1, 2, True, 6, \'v\', (1, 2, 1, 2)),)), (\'p\', (), ((4, 0, 7, 8, True, 30, \'v\', (7, 8, 7, 8)),))), (), ())", ("(((\'ge\', 0, 10),), (2, 1))",))': ('prj-listed-order', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 1, 4, True, 10, \'v\', (1, 2, 3, 4)),)), (\'p\', (), ((2, 0, 10, 20, True, 30, \'v\', (10, 20)),)), (\'p\', (), ((2, 0, 30, 40, True, 70, \'v\', (30, 40)),))), ((1, 0, \'7\'), (1, 1, \'None\')), ())", ("(((\'ge\', 0, 1),), (1,))",))': ('prj-moved-no-read', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 20, 30, True, 101, \'v\', (20, 24, 27, 30)),)), (\'p\', (), ((4, 2, 1, 2, True, 3, \'v\', (1, None, 2, None)),))), (), ())", ("(((\'ge\', 0, 10),), (1,))",))': ('prj-nulls-out', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 1, 4, True, 10, \'v\', (1, 2, 3, 4)),)), (\'d\', (20,), ((2, 0, 20, 20, False, 40, \'i\', (0, 0)), (2, 0, 20, 20, False, 40, \'v\', (20, 20))))), (), ())", ("(((\'le\', 0, 3),), (1,))",))': ('prj-one-entry-fallback', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 1, 9, True, 15, \'v\', (1, 9, 2, 3)),)), (\'d\', (20,), ((2, 1, 20, 20, False, 20, \'i\', (0, None)),)), (\'p\', (), ((2, 0, 30, 40, True, 70, \'v\', (30, 40)),))), (), ())", ("(((\'le\', 0, 3),), (1,))",))': ('prj-one-entry-nulls', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 1, 9, True, 15, \'v\', (1, 9, 2, 3)),)), (\'d\', (20,), ((2, 0, 20, 20, False, 40, \'i\', (0, 0)),)), (\'p\', (), ((2, 0, 30, 40, True, 70, \'v\', (30, 40)),))), (), ())", ("(((\'le\', 0, 3),), (1,))",))': ('prj-one-entry-rd', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 1, 9, True, 15, \'v\', (1, 9, 2, 3)),)), (\'p\', (), ((2, 0, 12, 12, True, 24, \'v\', (12, 12)),)), (\'p\', (), ((2, 0, 30, 40, True, 70, \'v\', (30, 40)),))), (), ())", ("(((\'le\', 0, 3),), (1,))",))': ('prj-pinned-no-read', 0), '("(10, 4, 2, ((\'p\', (), ((4, 1, 20, 30, True, 77, \'v\', (20, None, 27, 30)),)), (\'p\', (), ((4, 0, 1, 2, True, 6, \'v\', (1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 22),), (0,))",))': ('prj-reuse-read', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 20, 30, True, 101, \'v\', (20, 24, 27, 30)),)), (\'p\', (), ((4, 0, 1, 2, True, 6, \'v\', (1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 10),), (1, 1))",))': ('prj-same-twice', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 1, 9, True, 15, \'v\', (1, 9, 2, 3)),)), (\'p\', (), ((2, 2, None, None, True, 0, \'v\', (None, None)),)), (\'p\', (), ((2, 0, 30, 40, True, 70, \'v\', (30, 40)),))), (), ())", ("(((\'le\', 0, 3),), (1,))",))': ('prj-void-no-read', 0), '("(10, 6, 2, ((\'p\', (), ((3, 0, 1, 3, True, 6, \'v\', (1, 2, 3)), (3, 0, 7, 9, True, 24, \'v\', (7, 8, 9)))), (\'p\', (), ((3, 0, 10, 30, True, 60, \'v\', (10, 20, 30)), (3, 1, 40, 60, True, 100, \'v\', (40, None, 60))))), (), (4,))", ("(((\'ge\', 0, 5),), (1,))",))': ('prj-whole-broken-by-delete', 0), '("(10, 6, 2, ((\'p\', (), ((3, 0, 1, 3, True, 6, \'v\', (1, 2, 3)), (3, 0, 7, 9, True, 24, \'v\', (7, 8, 9)))), (\'p\', (), ((3, 0, 10, 30, True, 60, \'v\', (10, 20, 30)), (3, 1, 40, 60, True, 100, \'v\', (40, None, 60))))), ((1, 5, \'99\'),), ())", ("(((\'ge\', 0, 5),), (1,))",))': ('prj-whole-broken-by-update', 0), '("(10, 6, 2, ((\'p\', (), ((3, 0, 1, 3, True, 6, \'v\', (1, 2, 3)), (3, 0, 7, 9, True, 24, \'v\', (7, 8, 9)))), (\'p\', (), ((3, 0, 10, 30, True, 60, \'v\', (10, 20, 30)), (3, 1, 40, 60, True, 100, \'v\', (40, None, 60))))), (), ())", ("(((\'ge\', 0, 5),), (1,))",))': ('prj-whole-page-sum', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 1, 9, True, 15, \'v\', (1, 9, 2, 3)),)), (\'p\', (), ((2, 0, 20, 20, False, 40, \'v\', (20, 20)),)), (\'p\', (), ((2, 0, 30, 40, True, 70, \'v\', (30, 40)),))), (), ())", ("(((\'le\', 0, 3),), (1,))",))': ('prj-widened-not-pinned', 0), '("(10, 8, 2, ((\'d\', (3, 9), ((4, 0, 3, 9, True, 24, \'i\', (0, 1, 0, 1)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 5),), (1,))", "(((\'ge\', 0, 5),), (1,))"))': ('qry-starts-over', 1), '("(10, 8, 2, ((\'p\', (), ((4, 0, 5, 8, True, 26, \'v\', (5, 6, 7, 8)),)), (\'p\', (), ((4, 0, 40, 50, True, 181, \'v\', (40, 44, 47, 50)),)), (\'p\', (), ((8, 0, 1, 2, True, 12, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 60),), (0, 1))",))': ('sel-empty', 0), '("(10, 6, 2, ((\'d\', (0, 5, 9), ((3, 0, 0, 9, True, 14, \'i\', (0, 1, 2)),)), (\'p\', (), ((3, 0, 0, 9, True, 15, \'v\', (1, 6, 8)),)), (\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),))), ((0, 0, \'7\'), (0, 1, \'2\'), (0, 2, \'9\')), ())", ("(((\'ge\', 0, 5),), (1,))",))': ('upd-all-moved-no-rd', 0), '("(10, 6, 2, ((\'p\', (), ((3, 0, 0, 9, True, 14, \'v\', (0, 5, 9)),)), (\'p\', (), ((3, 0, 0, 9, True, 15, \'v\', (1, 6, 8)),)), (\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),))), ((0, 0, \'7\'), (0, 1, \'2\'), (0, 2, \'9\')), ())", ("(((\'ge\', 0, 5),), (1,))",))': ('upd-all-moved-no-read', 0), '("(25, 134, 2, ((\'p\', (), ((23, 21, 1, 2, True, 3, \'v\', (None, None, None, None, None, None, None, None, None, None, None, None, None, 2, None, None, None, None, None, None, None, 1, None)),)), (\'d\', (1, 2, 5), ((24, 19, 1, 5, True, 14, \'i\', (2, None, None, None, None, 2, None, None, 0, None, 1, None, 0, None, None, None, None, None, None, None, None, None, None, None)),)), (\'d\', (1,), ((29, 28, 1, 1, True, 1, \'i\', (None, None, None, None, None, None, None, None, None, 0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)),)), (\'p\', (), ((23, 23, None, None, True, 0, \'v\', (None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)),)), (\'d\', (2, 3), ((35, 32, 2, 3, True, 7, \'i\', (0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, 0, None, None, None, None, None, None, 1, None, None, None, None, None, None)),)), (\'p\', (), ((21, 19, 7, 8, True, 15, \'v\', (7, None, None, None, None, None, 8, None, None, None, None, None, None, None, None, None, None, None, None, None, None)),)), (\'p\', (), ((33, 31, 2, 11, True, 13, \'v\', (None, None, None, None, None, None, None, None, None, None, None, None, None, None, 11, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, 2, None)),)), (\'d\', (6, 11), ((16, 14, 6, 11, True, 17, \'i\', (None, None, None, None, 1, None, 0, None, None, None, None, None, None, None, None, None)),)), (\'d\', (0, 4), ((27, 24, 0, 0, False, 8, \'i\', (None, None, None, None, None, None, None, None, None, None, None, None, 1, None, None, None, None, None, None, None, None, None, None, 1, 0, None, None)),)), (\'d\', (6, 10), ((37, 35, 6, 10, True, 16, \'i\', (None, None, None, None, None, None, 1, None, None, None, None, None, None, None, 0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)),))), ((1, 38, \'8\'), (1, 41, \'0\')), ())", ("(((\'nn\', 1, 0), (\'nu\', 0, 0), (\'ge\', 1, 2)), (1,))",))': ('upd-count-as-written', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 5, 8, True, 26, \'v\', (5, 6, 7, 8)),)), (\'p\', (), ((4, 0, 1, 4, True, 10, \'v\', (1, 2, 3, 4)),))), ((0, 1, \'30\'),), ())", ("(((\'ge\', 0, 20),), (1, 0))",))': ('upd-drop-spares', 0), '("(10, 4, 2, ((\'p\', (), ((4, 0, 5, 8, True, 26, \'v\', (5, 6, 7, 8)),)), (\'p\', (), ((4, 0, 1, 4, True, 10, \'v\', (1, 2, 3, 4)),))), ((0, 2, \'1\'),), ())", ("(((\'ge\', 0, 3),), (1,))",))': ('upd-keep-tests', 0), '("(10, 6, 2, ((\'p\', (), ((6, 0, 1, 6, True, 21, \'v\', (1, 2, 3, 4, 5, 6)),)), (\'p\', (), ((3, 0, 0, 9, True, 14, \'v\', (0, 5, 9)),)), (\'p\', (), ((3, 0, 0, 9, True, 15, \'v\', (1, 6, 8)),))), ((1, 0, \'7\'), (1, 1, \'2\')), ())", ("(((\'le\', 0, 2), (\'ge\', 1, 5)), (0,))",))': ('upd-last-held-dies', 0)}


_LAST = [None, []]


def _fp(seg, q):
    if _LAST[0] is not seg:
        _LAST[0] = seg
        _LAST[1] = []
    _LAST[1].append(q)
    heads = tuple((ch.enc, tuple(ch.dic or ()),
                   tuple((pg.n, pg.nulls, pg.mn, pg.mx, pg.exact, pg.sum, pg.form, tuple(pg.toks))
                         for pg in ch.pages))
                  for col in seg.cols for ch in col)
    ups = tuple((c, r, repr(v)) for c, u in enumerate(seg.up) for r, v in sorted(u.items()))
    segfp = repr((seg.g, seg.n, seg.k, heads, ups, tuple(sorted(seg.gone))))
    hist = tuple(repr((tuple((cd.kind, cd.c, cd.v) for cd in x.conds), tuple(x.cols)))
                 for x in _LAST[1])
    return repr((segfp, hist))


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
