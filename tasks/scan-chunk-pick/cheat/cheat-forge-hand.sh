#!/bin/bash
# carries the frozen answers for every enumerated segment file
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
def run(seg, q, st, out):
    return
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
import json

_GT = json.loads(r'''{
 "dec-hits-over-page": [
  "qry 0",
  "dc 1 0 1",
  "sel 4 1000011000042000059",
  "dc 0 0 1",
  "prj 0 3 28",
  "qry 1",
  "dc 1 0 0",
  "dc 0 0 0",
  "sel 3 2000015000032",
  "prj 0 3 28"
 ],
 "dec-hits-whole-chunk": [
  "qry 0",
  "dc 0 0 0",
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
 "flt-consult-settles-whole-chunk": [
  "qry 0",
  "dc 1 0 0",
  "rd 0 0",
  "sel 0 0",
  "prj 0 0 0"
 ],
 "flt-dict-settles-every-page": [
  "qry 0",
  "rd 0 1",
  "rd 0 0",
  "dc 0 0 0",
  "sel 0 0",
  "prj 0 0 0"
 ],
 "flt-header-kills-at-start": [
  "qry 0",
  "sel 0 0",
  "prj 0 0 0"
 ],
 "flt-header-kills-other-column": [
  "qry 0",
  "dc 1 0 1",
  "sel 5 1063405581883279096",
  "prj 1 5 35"
 ],
 "flt-memory-kills-at-start": [
  "qry 0",
  "rd 1 0",
  "dc 1 0 1",
  "dc 1 0 2",
  "sel 5 2168782150117166810",
  "dc 0 1 0",
  "prj 0 5 86",
  "qry 1",
  "sel 1 4",
  "prj 1 1 45"
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
 "mem-counts-exact-from-start": [
  "qry 0",
  "dc 0 0 0",
  "sel 3 2000020000051",
  "prj 0 3 27",
  "qry 1",
  "dc 0 1 0",
  "dc 0 0 1",
  "sel 6 344031566752559980",
  "prj 0 6 40"
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
 "ord-read-counts-exact": [
  "qry 0",
  "dc 0 0 2",
  "sel 5 2168781150109166793",
  "prj 1 4 172",
  "qry 1",
  "dc 0 0 0",
  "dc 0 0 1",
  "dc 2 0 0",
  "sel 1 1",
  "prj 2 1 0"
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
  "rd 1 0",
  "dc 1 0 0",
  "dc 1 3 0",
  "rd 1 5",
  "dc 1 5 0",
  "rd 1 4",
  "dc 0 5 0",
  "rd 0 1",
  "dc 0 1 0",
  "sel 61 304011921253275645",
  "prj 0 61 180"
 ],
 "ord-read-raises-repush": [
  "qry 0",
  "dc 1 0 0",
  "dc 1 2 0",
  "dc 0 0 0",
  "dc 0 0 1",
  "sel 1 2",
  "prj 1 1 13"
 ],
 "ord-read-raises-stale": [
  "qry 0",
  "dc 0 0 0",
  "dc 0 0 1",
  "dc 0 0 2",
  "sel 9 1144753665323943236",
  "dc 1 1 0",
  "dc 1 4 0",
  "prj 1 9 216"
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
 "prj-chunk-sum-blocked": [
  "qry 0",
  "sel 6 1649866575945253913",
  "dc 0 0 0",
  "dc 0 0 2",
  "prj 0 6 30"
 ],
 "prj-chunk-sum-pinned-dead": [
  "qry 0",
  "sel 6 1649866575945253913",
  "prj 0 6 30"
 ],
 "prj-chunk-sum-together": [
  "qry 0",
  "sel 4 1000011000042000058",
  "prj 0 4 73"
 ],
 "prj-chunk-sum-update": [
  "qry 0",
  "sel 9 48757370013698165",
  "dc 0 1 1",
  "prj 0 9 100"
 ],
 "prj-chunk-sum-whole": [
  "qry 0",
  "sel 6 1649863575924253874",
  "prj 0 6 21"
 ],
 "prj-consult-needs-live-row": [
  "qry 0",
  "sel 3 4000029000057",
  "dc 0 0 1",
  "prj 0 3 12"
 ],
 "prj-consult-not-sparing": [
  "qry 0",
  "dc 1 0 0",
  "sel 5 1031708290962639577",
  "dc 0 0 0",
  "prj 0 3 30"
 ],
 "prj-consult-spares-read": [
  "qry 0",
  "dc 1 0 1",
  "sel 5 2232175731950445831",
  "rd 0 0",
  "prj 0 5 32"
 ],
 "prj-dead-chunk": [
  "qry 0",
  "sel 4 388364981750612316",
  "prj 1 4 14"
 ],
 "prj-dead-page-blocks-sum": [
  "qry 0",
  "sel 3 4000029000057",
  "dc 1 0 1",
  "prj 1 2 100"
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
 "prj-pinned-nulls-sum": [
  "qry 0",
  "sel 2 3000013",
  "prj 0 2 25"
 ],
 "prj-reads-in-page-order": [
  "qry 0",
  "sel 3 1000008000018",
  "dc 0 0 0",
  "dc 0 0 1",
  "prj 0 3 40"
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
  "dc 0 1 0",
  "dc 0 4 0",
  "rd 1 3",
  "dc 1 3 0",
  "dc 0 2 0",
  "sel 10 2206839713766188681",
  "prj 1 10 66"
 ],
 "upd-count-over-page-as-written": [
  "qry 0",
  "dc 0 1 1",
  "sel 2 7000029",
  "dc 1 1 1",
  "prj 1 2 7",
  "qry 1",
  "dc 0 0 0",
  "dc 0 1 0",
  "sel 5 2168781150110166800",
  "prj 0 5 65"
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
 ],
 "upd-read-not-merged": [
  "qry 0",
  "dc 0 0 1",
  "sel 5 2168781150109166795",
  "prj 0 5 214"
 ]
}
''')

_FP = {'("(5, 5, 2, ((\'p\', 36, (), ((2, 1, 10, 10, False, \'v\', (None, 10)), (3, 0, 1, 17, True, \'v\', (17, 8, 1)))), (\'p\', 9, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)), (2, 1, 3, 3, True, \'v\', (None, 3))))), (), ())", ("(((\'ge\', 1, 1),), (0,))",))': ('dec-hits-over-page', 0), '("(5, 5, 2, ((\'p\', 36, (), ((2, 1, 10, 10, False, \'v\', (None, 10)), (3, 0, 1, 17, True, \'v\', (17, 8, 1)))), (\'p\', 9, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)), (2, 1, 3, 3, True, \'v\', (None, 3))))), (), ())", ("(((\'ge\', 1, 1),), (0,))", "(((\'nn\', 0, 0), (\'ne\', 1, 1)), (0,))"))': ('dec-hits-over-page', 1), '("(10, 8, 3, ((\'p\', 56, (), ((8, 0, 5, 9, True, \'v\', (5, 5, 5, 5, 9, 9, 9, 9)),)), (\'p\', 0, (), ((4, 0, 0, 0, True, \'v\', (0, 0, 0, 0)),)), (\'p\', 4, (), ((4, 0, 1, 1, True, \'v\', (1, 1, 1, 1)),)), (\'p\', 36, (), ((8, 0, 1, 8, True, \'v\', (1, 2, 3, 4, 5, 6, 7, 8)),))), (), ())", ("(((\'ge\', 0, 6), (\'le\', 1, 0), (\'eq\', 0, 5), (\'le\', 2, 2)), (2,))",))': ('dec-hits-whole-chunk', 0), '("(10, 6, 2, ((\'p\', 14, (), ((3, 0, 0, 9, True, \'v\', (0, 5, 9)),)), (\'p\', 25, (), ((3, 0, 1, 20, True, \'v\', (1, 4, 20)),)), (\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),))), (), (0, 1))", ("(((\'le\', 0, 7),), (1,))",))': ('del-caps-score', 0), '("(10, 6, 2, ((\'p\', 6, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)),)), (\'p\', 15, (), ((3, 0, 4, 6, True, \'v\', (4, 5, 6)),)), (\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),))), (), (0, 1, 2))", ("(((\'ge\', 0, 2),), (1,))",))': ('del-never-alive', 0), '("(10, 8, 2, ((\'d\', 24, (3, 9), ((4, 0, 3, 9, True, \'i\', (0, 1, 0, 1)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ne\', 0, 5), (\'ge\', 0, 5)), (1,))",))': ('dic-charge-once', 0), '("(10, 8, 2, ((\'d\', 15, (3, 9), ((4, 1, 3, 9, True, \'i\', (0, None, 0, 1)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'eq\', 0, 5),), (1,))",))': ('dic-drop-with-nulls', 0), '("(10, 8, 2, ((\'d\', 15, (3, 9), ((4, 1, 3, 9, True, \'i\', (0, None, 0, 1)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'nn\', 0, 0),), (1,))",))': ('dic-not-for-null', 0), '("(10, 8, 2, ((\'d\', 15, (3, 9), ((4, 1, 3, 9, True, \'i\', (0, None, 0, 1)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ne\', 0, 5),), (1,))",))': ('dic-nulls-read', 0), '("(10, 8, 2, ((\'d\', 22, (3, 9), ((4, 0, 3, 9, True, \'v\', (3, 7, 3, 9)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'eq\', 0, 7),), (1,))",))': ('dic-overflow-read', 0), '("(10, 8, 2, ((\'d\', 24, (3, 9), ((4, 0, 3, 9, True, \'i\', (0, 1, 0, 1)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'eq\', 0, 5),), (1,))",))': ('dic-whole-drop', 0), '("(10, 8, 2, ((\'d\', 24, (3, 9), ((4, 0, 3, 9, True, \'i\', (0, 1, 0, 1)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ne\', 0, 5),), (1,))",))': ('dic-whole-keep', 0), '("(10, 8, 2, ((\'d\', 24, (3, 9), ((4, 0, 3, 9, True, \'i\', (0, 1, 0, 1)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 5),), (1,))",))': ('qry-starts-over', 0), '("(5, 5, 2, ((\'d\', 106, (17, 22, 25), ((2, 0, 17, 22, True, \'i\', (1, 0)), (2, 0, 20, 25, False, \'i\', (0, 2)), (1, 0, 25, 25, False, \'i\', (2,)))), (\'p\', 22, (), ((3, 0, 1, 18, True, \'v\', (3, 18, 1)),)), (\'p\', 28, (), ((2, 0, 10, 18, True, \'v\', (18, 10)),))), (), ())", ("(((\'ne\', 0, 20), (\'ge\', 1, 12), (\'eq\', 0, 24)), (0,))",))': ('flt-consult-settles-whole-chunk', 0), '("(5, 6, 1, ((\'d\', 20, (3, 4, 6, 7), ((2, 0, 3, 4, True, \'i\', (1, 0)), (2, 0, 6, 7, True, \'i\', (2, 3)))), (\'d\', 4, (0, 4), ((2, 0, 0, 4, True, \'i\', (0, 1)),))), (), ())", ("(((\'ge\', 0, 4), (\'eq\', 0, 3)), (0,))",))': ('flt-dict-settles-every-page', 0), '("(10, 5, 1, ((\'p\', 15, (), ((3, 0, 2, 7, True, \'v\', (7, 2, 6)), (2, 2, None, None, True, \'v\', (None, None)))),), (), ())", ("(((\'ge\', 0, 4), (\'nu\', 0, 0)), (0,))",))': ('flt-header-kills-at-start', 0), '("(10, 9, 2, ((\'p\', 10, (), ((3, 0, 1, 5, True, \'v\', (4, 1, 5)),)), (\'p\', 39, (), ((6, 0, 4, 9, True, \'v\', (4, 5, 6, 7, 8, 9)),)), (\'p\', 36, (), ((3, 0, 0, 0, True, \'v\', (0, 0, 0)), (6, 0, 1, 9, True, \'v\', (5, 6, 7, 8, 9, 1))))), (), ())", ("(((\'ge\', 0, 4), (\'ge\', 1, 5)), (1,))",))': ('flt-header-kills-other-column', 0), '("(10, 7, 2, ((\'p\', 29, (), ((2, 0, 11, 18, True, \'v\', (18, 11)),)), (\'p\', 15, (), ((2, 1, 15, 15, True, \'v\', (None, 15)),)), (\'p\', 58, (), ((1, 0, 16, 16, True, \'v\', (16,)), (2, 0, 16, 26, True, \'v\', (16, 26)))), (\'d\', 260, (40, 41, 42, 45, 46), ((1, 0, 40, 40, True, \'i\', (0,)), (3, 0, 41, 45, True, \'i\', (2, 1, 3)), (3, 1, 46, 46, True, \'i\', (None, 4, 4))))), (), ())", ("(((\'ne\', 1, 41),), (0,))",))': ('flt-memory-kills-at-start', 0), '("(10, 7, 2, ((\'p\', 29, (), ((2, 0, 11, 18, True, \'v\', (18, 11)),)), (\'p\', 15, (), ((2, 1, 15, 15, True, \'v\', (None, 15)),)), (\'p\', 58, (), ((1, 0, 16, 16, True, \'v\', (16,)), (2, 0, 16, 26, True, \'v\', (16, 26)))), (\'d\', 260, (40, 41, 42, 45, 46), ((1, 0, 40, 40, True, \'i\', (0,)), (3, 0, 41, 45, True, \'i\', (2, 1, 3)), (3, 1, 46, 46, True, \'i\', (None, 4, 4))))), (), ())", ("(((\'ne\', 1, 41),), (0,))", "(((\'ge\', 1, 43), (\'le\', 0, 15)), (1,))"))': ('flt-memory-kills-at-start', 1), '("(10, 8, 2, ((\'p\', 101, (), ((4, 0, 20, 30, True, \'v\', (20, 24, 27, 30)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 10),), (1,))",))': ('hdr-all-pass', 0), '("(10, 8, 2, ((\'p\', 26, (), ((4, 0, 5, 8, True, \'v\', (5, 6, 7, 8)),)), (\'p\', 101, (), ((4, 0, 20, 30, True, \'v\', (20, 24, 27, 30)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 22),), (1,))",))': ('hdr-miss-skip', 0), '("(10, 8, 2, ((\'p\', 28, (), ((4, 0, 7, 7, True, \'v\', (7, 7, 7, 7)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ne\', 0, 7),), (1,))",))': ('hdr-ne-exact-miss', 0), '("(10, 8, 2, ((\'p\', 101, (), ((4, 0, 20, 30, True, \'v\', (20, 24, 27, 30)),)), (\'p\', 87, (), ((4, 2, 40, 47, True, \'v\', (40, None, 47, None)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'nu\', 0, 0),), (0,))",))': ('hdr-nu-no-nulls', 0), '("(10, 8, 2, ((\'p\', 0, (), ((4, 4, None, None, True, \'v\', (None, None, None, None)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'nu\', 0, 0),), (1,))",))': ('hdr-null-chunk-null', 0), '("(10, 8, 2, ((\'p\', 0, (), ((4, 4, None, None, True, \'v\', (None, None, None, None)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'nu\', 0, 0),), (1,))", "(((\'nn\', 0, 0),), (1,))"))': ('hdr-null-chunk-null', 1), '("(10, 8, 2, ((\'p\', 45, (), ((4, 2, 20, 25, True, \'v\', (20, None, 25, None)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 10),), (1,))",))': ('hdr-nulls-block-pass', 0), '("(10, 4, 2, ((\'p\', 121, (), ((4, 0, 30, 30, False, \'v\', (28, 30, 33, 30)),)), (\'p\', 26, (), ((4, 0, 5, 8, True, \'v\', (5, 6, 7, 8)),))), (), ())", ("(((\'eq\', 0, 30),), (0,))",))': ('hdr-widen-eq', 0), '("(10, 4, 2, ((\'p\', 143, (), ((4, 0, 30, 40, False, \'v\', (21, 34, 48, 40)),)), (\'p\', 26, (), ((4, 0, 5, 8, True, \'v\', (5, 6, 7, 8)),))), (), ())", ("(((\'ge\', 0, 45),), (0,))",))': ('hdr-widen-high', 0), '("(10, 4, 2, ((\'p\', 143, (), ((4, 0, 30, 40, False, \'v\', (21, 34, 48, 40)),)), (\'p\', 26, (), ((4, 0, 5, 8, True, \'v\', (5, 6, 7, 8)),))), (), ())", ("(((\'le\', 0, 25),), (0,))",))': ('hdr-widen-low', 0), '("(10, 4, 2, ((\'p\', 121, (), ((4, 0, 30, 30, False, \'v\', (28, 30, 33, 30)),)), (\'p\', 26, (), ((4, 0, 5, 8, True, \'v\', (5, 6, 7, 8)),))), (), ())", ("(((\'ne\', 0, 30),), (0,))",))': ('hdr-widen-ne', 0), '("(10, 6, 2, ((\'d\', 33, (2, 9), ((6, 0, 2, 9, True, \'i\', (0, 1, 0, 1, 0, 1)),)), (\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),))), (), ())", ("(((\'eq\', 0, 5),), (1,))",))': ('mem-charge-across', 0), '("(10, 6, 2, ((\'d\', 33, (2, 9), ((6, 0, 2, 9, True, \'i\', (0, 1, 0, 1, 0, 1)),)), (\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),))), (), ())", ("(((\'eq\', 0, 5),), (1,))", "(((\'ne\', 0, 5),), (1,))"))': ('mem-charge-across', 1), '("(10, 6, 2, ((\'d\', 30, (2, 5, 8), ((6, 0, 2, 8, True, \'i\', (0, 1, 2, 0, 1, 2)),)), (\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),))), (), ())", ("(((\'ge\', 0, 3),), (1,))",))': ('mem-charge-once-file', 0), '("(10, 6, 2, ((\'d\', 30, (2, 5, 8), ((6, 0, 2, 8, True, \'i\', (0, 1, 2, 0, 1, 2)),)), (\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),))), (), ())", ("(((\'ge\', 0, 3),), (1,))", "(((\'le\', 0, 6),), (1,))"))': ('mem-charge-once-file', 1), '("(10, 9, 1, ((\'p\', 23, (), ((2, 0, 2, 9, True, \'v\', (2, 9)), (2, 0, 4, 8, True, \'v\', (4, 8)))), (\'p\', 21, (), ((3, 2, 3, 3, True, \'v\', (None, 3, None)), (2, 0, 9, 9, True, \'v\', (9, 9))))), (), ())", ("(((\'eq\', 0, 9),), (0,))",))': ('mem-counts-exact-from-start', 0), '("(10, 9, 1, ((\'p\', 23, (), ((2, 0, 2, 9, True, \'v\', (2, 9)), (2, 0, 4, 8, True, \'v\', (4, 8)))), (\'p\', 21, (), ((3, 2, 3, 3, True, \'v\', (None, 3, None)), (2, 0, 9, 9, True, \'v\', (9, 9))))), (), ())", ("(((\'eq\', 0, 9),), (0,))", "(((\'le\', 0, 9), (\'ne\', 0, 4)), (0,))"))': ('mem-counts-exact-from-start', 1), '("(10, 6, 2, ((\'p\', 180, (), ((3, 0, 50, 70, False, \'v\', (50, 60, 70)),)), (\'p\', 210, (), ((3, 0, 60, 80, True, \'v\', (60, 70, 80)),)), (\'p\', 24, (), ((3, 0, 7, 9, True, \'v\', (7, 8, 9)),)), (\'p\', 6, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)),))), (), ())", ("(((\'ge\', 0, 55),), (0,))",))': ('mem-exact-from-start', 0), '("(10, 6, 2, ((\'p\', 180, (), ((3, 0, 50, 70, False, \'v\', (50, 60, 70)),)), (\'p\', 210, (), ((3, 0, 60, 80, True, \'v\', (60, 70, 80)),)), (\'p\', 24, (), ((3, 0, 7, 9, True, \'v\', (7, 8, 9)),)), (\'p\', 6, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)),))), (), ())", ("(((\'ge\', 0, 55),), (0,))", "(((\'eq\', 1, 8), (\'le\', 0, 45)), (1,))"))': ('mem-exact-from-start', 1), '("(10, 6, 2, ((\'p\', 31, (), ((3, 0, 1, 9, True, \'v\', (1, 5, 9)), (3, 0, 2, 8, True, \'v\', (2, 6, 8)))), (\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),))), (), ())", ("(((\'ge\', 0, 5),), (1,))",))': ('mem-no-reread', 0), '("(10, 6, 2, ((\'p\', 31, (), ((3, 0, 1, 9, True, \'v\', (1, 5, 9)), (3, 0, 2, 8, True, \'v\', (2, 6, 8)))), (\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),))), (), ())", ("(((\'ge\', 0, 5),), (1,))", "(((\'le\', 0, 6),), (1,))"))': ('mem-no-reread', 1), '("(10, 6, 2, ((\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),)), (\'p\', 210, (), ((6, 0, 10, 60, True, \'v\', (10, 20, 30, 40, 50, 60)),))), (), ())", ("(((\'le\', 0, 4),), (1,))",))': ('mem-report-read-kept', 0), '("(10, 6, 2, ((\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),)), (\'p\', 210, (), ((6, 0, 10, 60, True, \'v\', (10, 20, 30, 40, 50, 60)),))), (), ())", ("(((\'le\', 0, 4),), (1,))", "(((\'ge\', 1, 25),), (0,))"))': ('mem-report-read-kept', 1), '("(10, 8, 2, ((\'p\', 87, (), ((8, 0, 10, 17, True, \'v\', (10, 10, 10, 10, 10, 10, 10, 17)),)), (\'p\', 6, (), ((4, 0, 0, 3, True, \'v\', (0, 1, 2, 3)),)), (\'p\', 6, (), ((4, 0, 0, 3, True, \'v\', (0, 1, 2, 3)),))), (), ())", ("(((\'ge\', 0, 15), (\'eq\', 0, 10), (\'le\', 1, 1)), (1,))",))': ('ord-exact-after-read', 0), '("(10, 8, 2, ((\'p\', 101, (), ((4, 0, 20, 30, True, \'v\', (20, 24, 27, 30)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 5), (\'le\', 1, 9)), (0, 1))",))': ('ord-keeps-all', 0), '("(10, 12, 2, ((\'p\', 90, (), ((6, 0, 10, 20, True, \'v\', (10, 12, 14, 16, 18, 20)),)), (\'p\', 95, (), ((6, 0, 11, 20, True, \'v\', (11, 13, 15, 17, 19, 20)),)), (\'p\', 141, (), ((4, 0, 30, 40, True, \'v\', (30, 34, 37, 40)),)), (\'p\', 144, (), ((4, 0, 31, 40, True, \'v\', (31, 35, 38, 40)),)), (\'p\', 147, (), ((4, 0, 32, 40, True, \'v\', (32, 36, 39, 40)),))), (), ())", ("(((\'ge\', 0, 12), (\'le\', 1, 38)), (0, 1))",))': ('ord-nothing-prunes', 0), '("(5, 6, 3, ((\'p\', 292, (), ((2, 0, 45, 52, True, \'v\', (52, 45)), (2, 0, 45, 50, False, \'v\', (44, 50)), (2, 0, 44, 57, True, \'v\', (44, 57)))), (\'p\', 172, (), ((4, 0, 41, 45, True, \'v\', (43, 43, 45, 41)),)), (\'p\', 0, (), ((2, 2, None, None, True, \'v\', (None, None)),)), (\'p\', 3, (), ((3, 1, 0, 2, True, \'v\', (0, None, 2)), (1, 0, 1, 1, True, \'v\', (1,)))), (\'p\', 0, (), ((2, 2, None, None, True, \'v\', (None, None)),))), (), ())", ("(((\'ne\', 0, 57),), (1,))",))': ('ord-read-counts-exact', 0), '("(5, 6, 3, ((\'p\', 292, (), ((2, 0, 45, 52, True, \'v\', (52, 45)), (2, 0, 45, 50, False, \'v\', (44, 50)), (2, 0, 44, 57, True, \'v\', (44, 57)))), (\'p\', 172, (), ((4, 0, 41, 45, True, \'v\', (43, 43, 45, 41)),)), (\'p\', 0, (), ((2, 2, None, None, True, \'v\', (None, None)),)), (\'p\', 3, (), ((3, 1, 0, 2, True, \'v\', (0, None, 2)), (1, 0, 1, 1, True, \'v\', (1,)))), (\'p\', 0, (), ((2, 2, None, None, True, \'v\', (None, None)),))), (), ())", ("(((\'ne\', 0, 57),), (1,))", "(((\'le\', 2, 1), (\'eq\', 0, 52)), (2,))"))': ('ord-read-counts-exact', 1), '("(10, 87, 2, ((\'p\', 37, (), ((15, 0, 0, 0, False, \'v\', (5, 1, 5, 3, 0, 1, 0, 3, 2, 4, 2, 1, 3, 5, 2)),)), (\'d\', 46, (0, 1, 2, 3, 4, 5), ((20, 1, 0, 5, True, \'i\', (2, 0, 4, 1, 0, 5, 1, 3, 3, 3, None, 4, 2, 1, 2, 1, 5, 4, 0, 5)),)), (\'d\', 26, (0, 1, 2, 3, 4, 5), ((15, 1, 0, 0, False, \'i\', (0, 4, 2, 4, 5, 2, 0, None, 0, 2, 1, 0, 3, 0, 3)),)), (\'d\', 19, (1, 2, 3, 5), ((10, 1, 0, 5, True, \'v\', (1, 0, 2, 0, 2, None, 3, 4, 2, 5)),)), (\'d\', 28, (0, 1, 2, 3, 4, 5), ((12, 0, 0, 0, False, \'i\', (0, 2, 3, 5, 2, 1, 3, 4, 2, 1, 2, 3)),)), (\'p\', 43, (), ((15, 2, 0, 5, True, \'v\', (4, None, 1, 3, 4, 5, 5, 4, 3, 2, 0, 5, None, 2, 5)),)), (\'d\', 23, (0, 1, 2, 3, 4, 5), ((11, 1, 0, 5, True, \'i\', (1, 1, 1, 5, 4, None, 5, 2, 0, 3, 1)),)), (\'d\', 25, (0, 1, 2, 3, 4, 5), ((12, 0, 0, 5, True, \'i\', (0, 0, 0, 1, 0, 2, 4, 4, 3, 2, 4, 5)),)), (\'d\', 35, (0, 1, 2, 3, 4, 5), ((15, 2, 0, 0, False, \'i\', (3, 5, 1, 1, 2, 5, None, 3, 4, None, 5, 4, 0, 1, 1)),)), (\'d\', 31, (0, 2, 3, 4), ((21, 4, 0, 0, False, \'v\', (5, 1, 3, 2, 0, 1, None, 0, None, None, 0, 4, 2, 0, 5, 1, 0, 2, 2, 3, None)),)), (\'d\', 45, (0, 1, 2, 3, 4, 5), ((18, 0, 0, 0, False, \'i\', (2, 2, 0, 4, 2, 2, 5, 0, 5, 3, 1, 5, 2, 5, 4, 1, 2, 0)),)), (\'d\', 31, (0, 2, 3, 4, 5), ((10, 1, 0, 5, True, \'i\', (4, 1, 4, 0, 4, 3, 1, 2, 4, None)),))), (), ())", ("(((\'ge\', 1, 0), (\'ge\', 0, 0), (\'ge\', 0, 1)), (0,))",))': ('ord-read-raises', 0), '("(10, 14, 2, ((\'p\', 638, (), ((3, 0, 28, 110, True, \'v\', (28, 110, 56)), (5, 0, 35, 53, True, \'v\', (36, 36, 35, 52, 53)), (6, 0, 35, 46, True, \'v\', (35, 37, 42, 46, 37, 35)))), (\'p\', 62, (), ((3, 0, 13, 32, True, \'v\', (17, 13, 32)),)), (\'p\', 19, (), ((1, 0, 19, 19, True, \'v\', (19,)),)), (\'p\', 42, (), ((4, 0, 4, 20, True, \'v\', (12, 6, 4, 20)),)), (\'p\', 9, (), ((1, 0, 9, 9, True, \'v\', (9,)),)), (\'p\', 79, (), ((4, 0, 11, 26, True, \'v\', (26, 11, 19, 23)),)), (\'p\', 37, (), ((1, 0, 37, 37, True, \'v\', (37,)),))), (), ())", ("(((\'ge\', 0, 35), (\'ge\', 0, 53), (\'le\', 1, 13)), (1,))",))': ('ord-read-raises-repush', 0), '("(10, 12, 2, ((\'p\', 989, (), ((3, 0, 38, 45, True, \'v\', (45, 45, 38)), (6, 0, 74, 145, True, \'v\', (129, 116, 145, 74, 132, 92)), (3, 0, 44, 65, True, \'v\', (65, 64, 44)))), (\'p\', 29, (), ((1, 0, 29, 29, True, \'v\', (29,)),)), (\'p\', 65, (), ((4, 0, 0, 35, True, \'v\', (4, 26, 35, 0)),)), (\'p\', 23, (), ((2, 0, 8, 15, True, \'v\', (15, 8)),)), (\'p\', 75, (), ((2, 0, 36, 39, True, \'v\', (39, 36)),)), (\'p\', 69, (), ((3, 0, 18, 32, True, \'v\', (32, 18, 19)),))), (), ())", ("(((\'ne\', 0, 116), (\'ge\', 0, 44), (\'ge\', 0, 45)), (1,))",))': ('ord-read-raises-stale', 0), '("(10, 66, 2, ((\'p\', 1082, (), ((14, 0, 43, 128, True, \'v\', (123, 107, 121, 112, 128, 53, 58, 60, 55, 65, 49, 59, 43, 49)),)), (\'p\', 1177, (), ((15, 0, 41, 112, True, \'v\', (100, 87, 66, 97, 112, 71, 41, 49, 98, 59, 42, 102, 73, 108, 72)),)), (\'p\', 962, (), ((11, 0, 51, 128, True, \'v\', (97, 78, 52, 93, 64, 92, 106, 77, 51, 128, 124)),)), (\'p\', 634, (), ((8, 0, 43, 124, True, \'v\', (75, 62, 43, 119, 124, 65, 101, 45)),)), (\'p\', 1648, (), ((18, 0, 42, 129, True, \'v\', (123, 129, 106, 42, 67, 117, 113, 61, 62, 87, 124, 122, 76, 82, 93, 47, 120, 77)),)), (\'p\', 319, (), ((15, 0, 7, 35, True, \'v\', (21, 30, 12, 28, 19, 27, 16, 35, 34, 18, 9, 35, 7, 10, 18)),)), (\'p\', 169, (), ((8, 0, 8, 32, True, \'v\', (9, 8, 29, 30, 27, 32, 21, 13)),)), (\'p\', 320, (), ((15, 0, 10, 36, True, \'v\', (22, 13, 17, 12, 17, 23, 10, 35, 29, 34, 26, 22, 36, 11, 13)),)), (\'p\', 225, (), ((11, 0, 7, 35, True, \'v\', (9, 35, 21, 25, 31, 7, 17, 10, 23, 31, 16)),)), (\'p\', 340, (), ((17, 0, 9, 36, True, \'v\', (16, 26, 17, 10, 11, 11, 17, 24, 18, 31, 36, 9, 30, 25, 13, 23, 23)),))), (), ())", ("(((\'ge\', 0, 51), (\'ne\', 0, 97)), (1,))",))': ('ord-read-rescored', 0), '("(10, 4, 2, ((\'p\', 24, (), ((4, 0, 3, 9, True, \'v\', (3, 5, 7, 9)),)), (\'p\', 1, (), ((2, 0, 0, 1, True, \'v\', (0, 1)),)), (\'p\', 1, (), ((2, 0, 0, 1, True, \'v\', (0, 1)),))), (), ())", ("(((\'eq\', 1, 1), (\'eq\', 0, 5)), (0,))",))': ('ord-spread-rounds-up', 0), '("(10, 4, 2, ((\'p\', 24, (), ((4, 0, 3, 9, True, \'v\', (3, 5, 7, 9)),)), (\'p\', 1, (), ((2, 0, 0, 1, True, \'v\', (0, 1)),)), (\'p\', 1, (), ((2, 0, 0, 1, True, \'v\', (0, 1)),))), (), ())", ("(((\'eq\', 1, 1), (\'ge\', 0, 9)), (0,))",))': ('ord-spread-takes-edge', 0), '("(10, 6, 2, ((\'p\', 180, (), ((2, 0, 50, 60, False, \'v\', (50, 60)), (1, 0, 70, 70, True, \'v\', (70,)))), (\'p\', 210, (), ((3, 0, 60, 80, True, \'v\', (60, 70, 80)),)), (\'p\', 24, (), ((3, 0, 7, 9, True, \'v\', (7, 8, 9)),)), (\'p\', 6, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)),))), (), ())", ("(((\'ge\', 0, 55),), (0,))",))': ('pg-count-mixed', 0), '("(10, 6, 2, ((\'p\', 180, (), ((2, 0, 50, 60, False, \'v\', (50, 60)), (1, 0, 70, 70, True, \'v\', (70,)))), (\'p\', 210, (), ((3, 0, 60, 80, True, \'v\', (60, 70, 80)),)), (\'p\', 24, (), ((3, 0, 7, 9, True, \'v\', (7, 8, 9)),)), (\'p\', 6, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)),))), (), ())", ("(((\'ge\', 0, 55),), (0,))", "(((\'eq\', 1, 8), (\'le\', 0, 45)), (1,))"))': ('pg-count-mixed', 1), '("(10, 4, 2, ((\'d\', 80, (20, 30), ((2, 0, 20, 30, False, \'i\', (0, 1)), (2, 1, 30, 30, False, \'i\', (1, None)))), (\'p\', 10, (), ((4, 0, 1, 4, True, \'v\', (1, 2, 3, 4)),))), (), ())", ("(((\'ge\', 0, 15),), (1,))",))': ('pg-dict-keep-page-nulls', 0), '("(10, 7, 2, ((\'d\', 37, (3, 4, 12), ((4, 0, 3, 12, True, \'i\', (0, 1, 0, 2)), (3, 0, 3, 8, True, \'v\', (3, 8, 4)))), (\'p\', 28, (), ((7, 0, 1, 7, True, \'v\', (1, 2, 3, 4, 5, 6, 7)),))), (), ())", ("(((\'eq\', 0, 8),), (1,))",))': ('pg-dict-skips-fallback', 0), '("(10, 9, 2, ((\'p\', 107, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)), (3, 0, 5, 12, True, \'v\', (5, 9, 12)), (3, 0, 20, 30, True, \'v\', (20, 25, 30)))), (\'p\', 45, (), ((9, 0, 1, 9, True, \'v\', (1, 2, 3, 4, 5, 6, 7, 8, 9)),))), (), ())", ("(((\'ge\', 0, 10),), (1,))",))': ('pg-partial-read', 0), '("(10, 9, 2, ((\'p\', 45, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)), (3, 0, 4, 6, True, \'v\', (4, 5, 6)), (3, 0, 7, 9, True, \'v\', (7, 8, 9)))), (\'p\', 78, (), ((3, 0, 10, 12, True, \'v\', (10, 11, 12)), (3, 0, 0, 2, True, \'v\', (0, 1, 2)), (3, 0, 13, 15, True, \'v\', (13, 14, 15))))), (), ())", ("(((\'ge\', 1, 10),), (0,))",))': ('prj-chunk-sum-blocked', 0), '("(10, 9, 2, ((\'p\', 40, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)), (3, 1, 5, 5, True, \'v\', (5, None, 5)), (3, 0, 7, 9, True, \'v\', (7, 8, 9)))), (\'p\', 78, (), ((3, 0, 10, 12, True, \'v\', (10, 11, 12)), (3, 0, 0, 2, True, \'v\', (0, 1, 2)), (3, 0, 13, 15, True, \'v\', (13, 14, 15))))), (), ())", ("(((\'ge\', 1, 10),), (0,))",))': ('prj-chunk-sum-pinned-dead', 0), '("(5, 4, 1, ((\'p\', 73, (), ((2, 0, 12, 16, True, \'v\', (16, 12)), (2, 0, 19, 26, True, \'v\', (26, 19)))),), (), ())", ("(((\'ge\', 0, 11),), (0,))",))': ('prj-chunk-sum-together', 0), '("(5, 9, 1, ((\'p\', 58, (), ((3, 0, 10, 12, True, \'v\', (10, 11, 12)), (2, 0, 12, 13, True, \'v\', (12, 13)))), (\'p\', 42, (), ((2, 0, 10, 11, True, \'v\', (10, 11)), (2, 0, 10, 11, True, \'v\', (10, 11))))), ((0, 7, \'10\'),), ())", ("(((\'ge\', 0, 10),), (0,))",))': ('prj-chunk-sum-update', 0), '("(10, 6, 2, ((\'p\', 21, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)), (3, 0, 4, 6, True, \'v\', (4, 5, 6)))), (\'p\', 60, (), ((6, 0, 5, 15, True, \'v\', (5, 7, 9, 11, 13, 15)),))), (), ())", ("(((\'ge\', 1, 5),), (0,))",))': ('prj-chunk-sum-whole', 0), '("(10, 6, 2, ((\'d\', 42, (10,), ((3, 0, 10, 10, False, \'i\', (0, 0, 0)), (3, 0, 3, 5, True, \'v\', (3, 4, 5)))), (\'p\', 24, (), ((3, 0, 0, 0, True, \'v\', (0, 0, 0)), (3, 0, 7, 9, True, \'v\', (7, 8, 9))))), (), ())", ("(((\'ge\', 1, 5),), (0,))",))': ('prj-consult-needs-live-row', 0), '("(10, 6, 2, ((\'d\', 40, (10,), ((3, 1, 10, 10, False, \'i\', (0, None, 0)), (3, 1, 10, 10, False, \'i\', (0, 0, None)))), (\'p\', 42, (), ((3, 0, 1, 9, True, \'v\', (1, 8, 9)), (3, 0, 7, 9, True, \'v\', (7, 8, 9))))), (), ())", ("(((\'ge\', 1, 5),), (0,))",))': ('prj-consult-not-sparing', 0), '("(10, 9, 2, ((\'d\', 72, (10,), ((3, 0, 10, 10, False, \'i\', (0, 0, 0)), (3, 0, 10, 10, False, \'i\', (0, 0, 0)), (3, 0, 3, 5, True, \'v\', (3, 4, 5)))), (\'p\', 42, (), ((3, 0, 0, 0, True, \'v\', (0, 0, 0)), (3, 0, 1, 9, True, \'v\', (1, 8, 9)), (3, 0, 7, 9, True, \'v\', (7, 8, 9))))), (), ())", ("(((\'ge\', 1, 5),), (0,))",))': ('prj-consult-spares-read', 0), '("(10, 8, 2, ((\'p\', 26, (), ((4, 0, 5, 8, True, \'v\', (5, 6, 7, 8)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 6, (), ((4, 0, 1, 2, True, \'v\', (1, 2, 1, 2)),)), (\'p\', 14, (), ((4, 0, 3, 4, True, \'v\', (3, 4, 3, 4)),))), (), ())", ("(((\'ge\', 0, 20),), (1,))",))': ('prj-dead-chunk', 0), '("(10, 6, 2, ((\'p\', 30, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)), (3, 0, 7, 9, True, \'v\', (7, 8, 9)))), (\'p\', 160, (), ((3, 0, 10, 30, True, \'v\', (10, 20, 30)), (3, 1, 40, 60, True, \'v\', (40, None, 60))))), (), ())", ("(((\'ge\', 0, 5),), (1,))",))': ('prj-dead-page-blocks-sum', 0), '("(10, 4, 3, ((\'p\', 101, (), ((4, 0, 20, 30, True, \'v\', (20, 24, 27, 30)),)), (\'p\', 6, (), ((4, 0, 1, 2, True, \'v\', (1, 2, 1, 2)),)), (\'p\', 30, (), ((4, 0, 7, 8, True, \'v\', (7, 8, 7, 8)),))), (), ())", ("(((\'ge\', 0, 10),), (2, 1))",))': ('prj-listed-order', 0), '("(10, 4, 2, ((\'p\', 10, (), ((4, 0, 1, 4, True, \'v\', (1, 2, 3, 4)),)), (\'p\', 30, (), ((2, 0, 10, 20, True, \'v\', (10, 20)),)), (\'p\', 70, (), ((2, 0, 30, 40, True, \'v\', (30, 40)),))), ((1, 0, \'7\'), (1, 1, \'None\')), ())", ("(((\'ge\', 0, 1),), (1,))",))': ('prj-moved-no-read', 0), '("(10, 4, 2, ((\'p\', 101, (), ((4, 0, 20, 30, True, \'v\', (20, 24, 27, 30)),)), (\'p\', 3, (), ((4, 2, 1, 2, True, \'v\', (1, None, 2, None)),))), (), ())", ("(((\'ge\', 0, 10),), (1,))",))': ('prj-nulls-out', 0), '("(10, 4, 2, ((\'p\', 10, (), ((4, 0, 1, 4, True, \'v\', (1, 2, 3, 4)),)), (\'d\', 80, (20,), ((2, 0, 20, 20, False, \'i\', (0, 0)), (2, 0, 20, 20, False, \'v\', (20, 20))))), (), ())", ("(((\'le\', 0, 3),), (1,))",))': ('prj-one-entry-fallback', 0), '("(10, 4, 2, ((\'p\', 15, (), ((4, 0, 1, 9, True, \'v\', (1, 9, 2, 3)),)), (\'d\', 20, (20,), ((2, 1, 20, 20, False, \'i\', (0, None)),)), (\'p\', 70, (), ((2, 0, 30, 40, True, \'v\', (30, 40)),))), (), ())", ("(((\'le\', 0, 3),), (1,))",))': ('prj-one-entry-nulls', 0), '("(10, 4, 2, ((\'p\', 15, (), ((4, 0, 1, 9, True, \'v\', (1, 9, 2, 3)),)), (\'d\', 40, (20,), ((2, 0, 20, 20, False, \'i\', (0, 0)),)), (\'p\', 70, (), ((2, 0, 30, 40, True, \'v\', (30, 40)),))), (), ())", ("(((\'le\', 0, 3),), (1,))",))': ('prj-one-entry-rd', 0), '("(10, 4, 2, ((\'p\', 15, (), ((4, 0, 1, 9, True, \'v\', (1, 9, 2, 3)),)), (\'p\', 24, (), ((2, 0, 12, 12, True, \'v\', (12, 12)),)), (\'p\', 70, (), ((2, 0, 30, 40, True, \'v\', (30, 40)),))), (), ())", ("(((\'le\', 0, 3),), (1,))",))': ('prj-pinned-no-read', 0), '("(10, 4, 1, ((\'d\', 36, (11, 12, 13), ((2, 1, 11, 11, True, \'i\', (0, None)), (2, 0, 12, 13, True, \'v\', (13, 12)))),), (), ())", ("(((\'ge\', 0, 12),), (0,))",))': ('prj-pinned-nulls-sum', 0), '("(10, 7, 2, ((\'p\', 95, (), ((2, 0, 12, 15, True, \'v\', (12, 15)), (3, 0, 13, 15, True, \'v\', (13, 13, 15)), (2, 0, 13, 14, True, \'v\', (14, 13)))), (\'p\', 17, (), ((3, 0, 1, 11, True, \'v\', (5, 1, 11)),)), (\'p\', 0, (), ((1, 1, None, None, True, \'v\', (None,)), (3, 3, None, None, True, \'v\', (None, None, None))))), (), ())", ("(((\'nn\', 1, 0),), (0,))",))': ('prj-reads-in-page-order', 0), '("(10, 4, 2, ((\'p\', 77, (), ((4, 1, 20, 30, True, \'v\', (20, None, 27, 30)),)), (\'p\', 6, (), ((4, 0, 1, 2, True, \'v\', (1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 22),), (0,))",))': ('prj-reuse-read', 0), '("(10, 4, 2, ((\'p\', 101, (), ((4, 0, 20, 30, True, \'v\', (20, 24, 27, 30)),)), (\'p\', 6, (), ((4, 0, 1, 2, True, \'v\', (1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 10),), (1, 1))",))': ('prj-same-twice', 0), '("(10, 4, 2, ((\'p\', 15, (), ((4, 0, 1, 9, True, \'v\', (1, 9, 2, 3)),)), (\'p\', 0, (), ((2, 2, None, None, True, \'v\', (None, None)),)), (\'p\', 70, (), ((2, 0, 30, 40, True, \'v\', (30, 40)),))), (), ())", ("(((\'le\', 0, 3),), (1,))",))': ('prj-void-no-read', 0), '("(10, 6, 2, ((\'p\', 30, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)), (3, 0, 7, 9, True, \'v\', (7, 8, 9)))), (\'p\', 160, (), ((3, 0, 10, 30, True, \'v\', (10, 20, 30)), (3, 1, 40, 60, True, \'v\', (40, None, 60))))), (), (4,))", ("(((\'ge\', 0, 5),), (1,))",))': ('prj-whole-broken-by-delete', 0), '("(10, 6, 2, ((\'p\', 30, (), ((3, 0, 1, 3, True, \'v\', (1, 2, 3)), (3, 0, 7, 9, True, \'v\', (7, 8, 9)))), (\'p\', 160, (), ((3, 0, 10, 30, True, \'v\', (10, 20, 30)), (3, 1, 40, 60, True, \'v\', (40, None, 60))))), ((1, 5, \'99\'),), ())", ("(((\'ge\', 0, 5),), (1,))",))': ('prj-whole-broken-by-update', 0), '("(10, 4, 2, ((\'p\', 15, (), ((4, 0, 1, 9, True, \'v\', (1, 9, 2, 3)),)), (\'p\', 40, (), ((2, 0, 20, 20, False, \'v\', (20, 20)),)), (\'p\', 70, (), ((2, 0, 30, 40, True, \'v\', (30, 40)),))), (), ())", ("(((\'le\', 0, 3),), (1,))",))': ('prj-widened-not-pinned', 0), '("(10, 8, 2, ((\'d\', 24, (3, 9), ((4, 0, 3, 9, True, \'i\', (0, 1, 0, 1)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 5),), (1,))", "(((\'ge\', 0, 5),), (1,))"))': ('qry-starts-over', 1), '("(10, 8, 2, ((\'p\', 26, (), ((4, 0, 5, 8, True, \'v\', (5, 6, 7, 8)),)), (\'p\', 181, (), ((4, 0, 40, 50, True, \'v\', (40, 44, 47, 50)),)), (\'p\', 12, (), ((8, 0, 1, 2, True, \'v\', (1, 2, 1, 2, 1, 2, 1, 2)),))), (), ())", ("(((\'ge\', 0, 60),), (0, 1))",))': ('sel-empty', 0), '("(10, 6, 2, ((\'d\', 14, (0, 5, 9), ((3, 0, 0, 9, True, \'i\', (0, 1, 2)),)), (\'p\', 15, (), ((3, 0, 1, 8, True, \'v\', (1, 6, 8)),)), (\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),))), ((0, 0, \'7\'), (0, 1, \'2\'), (0, 2, \'9\')), ())", ("(((\'ge\', 0, 5),), (1,))",))': ('upd-all-moved-no-rd', 0), '("(10, 6, 2, ((\'p\', 14, (), ((3, 0, 0, 9, True, \'v\', (0, 5, 9)),)), (\'p\', 15, (), ((3, 0, 1, 8, True, \'v\', (1, 6, 8)),)), (\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),))), ((0, 0, \'7\'), (0, 1, \'2\'), (0, 2, \'9\')), ())", ("(((\'ge\', 0, 5),), (1,))",))': ('upd-all-moved-no-read', 0), '("(25, 134, 2, ((\'p\', 3, (), ((23, 21, 1, 2, True, \'v\', (None, None, None, None, None, None, None, None, None, None, None, None, None, 2, None, None, None, None, None, None, None, 1, None)),)), (\'d\', 14, (1, 2, 5), ((24, 19, 1, 5, True, \'i\', (2, None, None, None, None, 2, None, None, 0, None, 1, None, 0, None, None, None, None, None, None, None, None, None, None, None)),)), (\'d\', 1, (1,), ((29, 28, 1, 1, True, \'i\', (None, None, None, None, None, None, None, None, None, 0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)),)), (\'p\', 0, (), ((23, 23, None, None, True, \'v\', (None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)),)), (\'d\', 7, (2, 3), ((35, 32, 2, 3, True, \'i\', (0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, 0, None, None, None, None, None, None, 1, None, None, None, None, None, None)),)), (\'p\', 15, (), ((21, 19, 7, 8, True, \'v\', (7, None, None, None, None, None, 8, None, None, None, None, None, None, None, None, None, None, None, None, None, None)),)), (\'p\', 13, (), ((33, 31, 2, 11, True, \'v\', (None, None, None, None, None, None, None, None, None, None, None, None, None, None, 11, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, 2, None)),)), (\'d\', 17, (6, 11), ((16, 14, 6, 11, True, \'i\', (None, None, None, None, 1, None, 0, None, None, None, None, None, None, None, None, None)),)), (\'d\', 8, (0, 4), ((27, 24, 0, 0, False, \'i\', (None, None, None, None, None, None, None, None, None, None, None, None, 1, None, None, None, None, None, None, None, None, None, None, 1, 0, None, None)),)), (\'d\', 16, (6, 10), ((37, 35, 6, 10, True, \'i\', (None, None, None, None, None, None, 1, None, None, None, None, None, None, None, 0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)),))), ((1, 38, \'8\'), (1, 41, \'0\')), ())", ("(((\'nn\', 1, 0), (\'nu\', 0, 0), (\'ge\', 1, 2)), (1,))",))': ('upd-count-as-written', 0), '("(10, 9, 2, ((\'p\', 56, (), ((4, 0, 10, 17, True, \'v\', (17, 14, 10, 15)),)), (\'p\', 56, (), ((2, 0, 13, 15, True, \'v\', (13, 15)), (3, 1, 11, 17, True, \'v\', (17, None, 11)))), (\'p\', 0, (), ((1, 1, None, None, True, \'v\', (None,)), (1, 1, None, None, True, \'v\', (None,)), (2, 2, None, None, True, \'v\', (None, None)), (2, 2, None, None, True, \'v\', (None, None)))), (\'p\', 13, (), ((1, 0, 2, 2, True, \'v\', (2,)), (2, 0, 5, 6, True, \'v\', (5, 6))))), ((0, 6, \'None\'),), ())", ("(((\'nu\', 0, 0),), (1,))",))': ('upd-count-over-page-as-written', 0), '("(10, 9, 2, ((\'p\', 56, (), ((4, 0, 10, 17, True, \'v\', (17, 14, 10, 15)),)), (\'p\', 56, (), ((2, 0, 13, 15, True, \'v\', (13, 15)), (3, 1, 11, 17, True, \'v\', (17, None, 11)))), (\'p\', 0, (), ((1, 1, None, None, True, \'v\', (None,)), (1, 1, None, None, True, \'v\', (None,)), (2, 2, None, None, True, \'v\', (None, None)), (2, 2, None, None, True, \'v\', (None, None)))), (\'p\', 13, (), ((1, 0, 2, 2, True, \'v\', (2,)), (2, 0, 5, 6, True, \'v\', (5, 6))))), ((0, 6, \'None\'),), ())", ("(((\'nu\', 0, 0),), (1,))", "(((\'ne\', 0, 15),), (0,))"))': ('upd-count-over-page-as-written', 1), '("(10, 4, 2, ((\'p\', 26, (), ((4, 0, 5, 8, True, \'v\', (5, 6, 7, 8)),)), (\'p\', 10, (), ((4, 0, 1, 4, True, \'v\', (1, 2, 3, 4)),))), ((0, 1, \'30\'),), ())", ("(((\'ge\', 0, 20),), (1, 0))",))': ('upd-drop-spares', 0), '("(10, 4, 2, ((\'p\', 26, (), ((4, 0, 5, 8, True, \'v\', (5, 6, 7, 8)),)), (\'p\', 10, (), ((4, 0, 1, 4, True, \'v\', (1, 2, 3, 4)),))), ((0, 2, \'1\'),), ())", ("(((\'ge\', 0, 3),), (1,))",))': ('upd-keep-tests', 0), '("(10, 6, 2, ((\'p\', 21, (), ((6, 0, 1, 6, True, \'v\', (1, 2, 3, 4, 5, 6)),)), (\'p\', 14, (), ((3, 0, 0, 9, True, \'v\', (0, 5, 9)),)), (\'p\', 15, (), ((3, 0, 1, 8, True, \'v\', (1, 6, 8)),))), ((1, 0, \'7\'), (1, 1, \'2\')), ())", ("(((\'le\', 0, 2), (\'ge\', 1, 5)), (0,))",))': ('upd-last-held-dies', 0), '("(10, 7, 1, ((\'p\', 263, (), ((2, 0, 42, 44, True, \'v\', (44, 42)), (2, 0, 42, 46, True, \'v\', (42, 46)), (2, 1, 45, 45, True, \'v\', (None, 45)), (1, 0, 44, 44, True, \'v\', (44,)))),), ((0, 3, \'42\'),), ())", ("(((\'le\', 0, 44),), (0,))",))': ('upd-read-not-merged', 0)}


_LAST = [None, []]


def _fp(seg, q):
    if _LAST[0] is not seg:
        _LAST[0] = seg
        _LAST[1] = []
    _LAST[1].append(q)
    heads = tuple((ch.enc, ch.sum, tuple(ch.dic or ()),
                   tuple((pg.n, pg.nulls, pg.mn, pg.mx, pg.exact, pg.form, tuple(pg.toks))
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
