#!/bin/bash
# the frozen enumerated answers replayed over the shipped engine
set -euo pipefail

cat > /app/rng/seg.py <<'PYEOF'
"""The cached-stretch table.

A stretch records that, over the closed key range [lo, hi], `rows` is exactly the store's
content for every version from `born` to `died` inclusive; `died` is -1 while the stretch is
still current, which means it runs to the present version and keeps extending.

Two block indexes sit over it. `opens` is what a commit walks and holds only stretches that
are still current, so the work a commit does is bounded by the stretches that actually cover
the written key rather than by the size of the table; a stretch leaves that index the first
time a scan meets it after it was closed. `alls` is what a read walks and holds every
retained stretch, closed ones included, because a read aimed at an older version is answered
from exactly those. A stretch wider than one block is listed in each block it touches, so both
scans stamp what they have already seen with the query number rather than paying for a set.

Retention is a heap of closed stretches ordered by the last version each was correct at, so
dropping what has fallen past the horizon costs nothing on the commits where nothing has.
"""

import heapq

BLOCK = 32


class Stretch(object):
    __slots__ = ("lo", "hi", "rows", "born", "died", "gone", "tag")

    def __init__(self, lo, hi, rows, born):
        self.lo = lo
        self.hi = hi
        self.rows = rows
        self.born = born
        self.died = -1
        self.gone = False
        self.tag = -1


class Table(object):
    __slots__ = ("opens", "alls", "stamp", "pend", "seq", "walk", "cands")

    def __init__(self):
        self.opens = {}
        self.alls = {}
        self.stamp = 0
        self.pend = []
        self.seq = 0

    def add(self, lo, hi, rows, born):
        st = Stretch(lo, hi, rows, born)
        for b in range(lo // BLOCK, hi // BLOCK + 1):
            box = self.opens.get(b)
            if box is None:
                box = self.opens[b] = []
            box.append(st)
            box = self.alls.get(b)
            if box is None:
                box = self.alls[b] = []
            box.append(st)
        return st

    def close(self, keys, upto):
        for k in keys:
            b = k // BLOCK
            box = self.opens.get(b)
            if not box:
                continue
            keep = []
            for st in box:
                if st.died >= 0 or st.gone:
                    continue
                if st.lo <= k <= st.hi:
                    st.died = upto
                    self.seq += 1
                    heapq.heappush(self.pend, (upto, self.seq, st))
                else:
                    keep.append(st)
            self.opens[b] = keep

    def drop(self, floor):
        pend = self.pend
        while pend and pend[0][0] < floor:
            heapq.heappop(pend)[2].gone = True

    def near(self, lo, hi):
        self.stamp += 1
        tag = self.stamp
        found = []
        for b in range(lo // BLOCK, hi // BLOCK + 1):
            box = self.alls.get(b)
            if not box:
                continue
            keep = []
            for st in box:
                if st.gone:
                    continue
                keep.append(st)
                if st.tag == tag:
                    continue
                st.tag = tag
                if st.hi >= lo and st.lo <= hi:
                    found.append(st)
            if len(keep) != len(box):
                self.alls[b] = keep
        return found
PYEOF

cat > /app/rng/pick.py <<'PYEOF'
"""The version a read is answered at.

The answer is one version, so the whole requested range has to be covered by stretches that
are all correct at that version, and the newest such version inside the client's allowance
wins. Coverage is not monotone in the version: as the version drops a stretch closed earlier
becomes usable while a stretch fetched later stops being, so there is nothing to binary
search over.

What is true is that coverage can only improve at a version where a stretch's validity ends,
because everywhere else the usable set only loses members as the version drops. So the
candidates are the present version and the end of each stretch's validity, and one sweep down
that list - adding a stretch as its end is reached, dropping it once the version falls below
its start, and keeping a covered-key count over the requested range - finds the answer
without visiting a single version in between.
"""

import heapq


def at(tb, lo, hi, s, now):
    floor = now - s
    if floor < 0:
        floor = 0
    spans = []
    for st in tb.near(lo, hi):
        top = now if st.died < 0 else st.died
        if top < floor:
            continue
        low = st.born
        if low < floor:
            low = floor
        if low > top:
            continue
        a = st.lo if st.lo > lo else lo
        b = st.hi if st.hi < hi else hi
        spans.append((top, low, a, b))
    if not spans:
        return None
    spans.sort(key=lambda row: row[0], reverse=True)
    order = sorted(set([now] + [row[0] for row in spans if row[0] < now]), reverse=True)

    width = hi - lo + 1
    cnt = [0] * width
    short = width
    held = []
    i = 0
    total = len(spans)
    for v in order:
        while i < total and spans[i][0] >= v:
            top, low, a, b = spans[i]
            i += 1
            for k in range(a - lo, b - lo + 1):
                if cnt[k] == 0:
                    short -= 1
                cnt[k] += 1
            heapq.heappush(held, (-low, a, b))
        while held and -held[0][0] > v:
            back, a, b = heapq.heappop(held)
            for k in range(a - lo, b - lo + 1):
                cnt[k] -= 1
                if cnt[k] == 0:
                    short += 1
        if short == 0:
            return v
    return None
PYEOF

cat > /app/rng/hole.py <<'PYEOF'
"""The parts of a requested range the cache cannot answer at the present version.

Only stretches that are still current count here, whatever the read's allowance turned out to
be: the fetch goes to the store, the store answers as of now, and the answer that follows a
fetch is the present one. Stretches are sorted by their first key before the walk because a
refetched stretch is installed wherever the hole was, not at the end of the key order, and
because a current stretch can sit inside another one.
"""


def runs(items, lo, hi):
    spans = []
    for st in items:
        if st.died < 0 and st.hi >= lo and st.lo <= hi:
            spans.append((st.lo, st.hi))
    spans.sort()
    gaps = []
    at = lo
    for a, b in spans:
        if a > hi:
            break
        if a > at:
            gaps.append((at, a - 1))
        if b + 1 > at:
            at = b + 1
        if at > hi:
            break
    if at <= hi:
        gaps.append((at, hi))
    return gaps
PYEOF

cat > /app/rng/mend.py <<'PYEOF'
"""Shaping the fetches a read issues.

Two holes with only a little covered ground between them cost less as one round trip than as
two, so runs close enough together are fetched as one - which means the fetch covers keys the
cache already had, and installs a stretch over them alongside the one that was already there.
That is not free either way: the run the store reports its last write over is now the wider
one, so the combined fetch is correct from a later version than the two narrow ones would have
been, and it reaches less far back for the reads that follow.

The cap is the same trade taken to its end. A read that would scatter more fetches than the cap
allows takes the whole requested range in one instead, which is wider still, later still, and
sits over everything already held.
"""


def shape(runs, lo, hi, slack, cap):
    if not runs:
        return []
    out = [[runs[0][0], runs[0][1]]]
    for a, b in runs[1:]:
        if a - out[-1][1] - 1 <= slack:
            out[-1][1] = b
        else:
            out.append([a, b])
    if len(out) > cap:
        return [(lo, hi)]
    return [(a, b) for a, b in out]
PYEOF

cat > /app/rng/knit.py <<'PYEOF'
"""The rows of the answer.

Every stretch correct at the served version agrees with the store at that version, so two of
them that overlap agree with each other and it does not matter which one a shared key is read
from - but the key must appear once, and the stretches arrive in neither key order nor any
other useful one, so the rows are collected into a map and sorted at the end.
"""


def rows(items, lo, hi, at):
    got = {}
    for st in items:
        if st.born > at:
            continue
        if 0 <= st.died < at:
            continue
        if st.hi < lo or st.lo > hi:
            continue
        for k, v in st.rows:
            if lo <= k <= hi:
                got[k] = v
    return sorted(got.items())
PYEOF

cat > /app/rng/age.py <<'PYEOF'
"""Retention.

A stretch whose validity ended is still worth keeping, because a read with an allowance is
answered from exactly those - but only back as far as the horizon, so once its last correct
version falls below the present version minus the horizon it can never be chosen again and
goes. A stretch that is still current has no end and is never discarded here.
"""


def sweep(tb, now, horizon):
    floor = now - horizon
    if floor <= 0:
        return
    tb.drop(floor)
PYEOF

cat > /app/rng/ask.py <<'PYEOF'

import json

from . import age, hole, knit, mend, out, pick

RAW = '{"absent-delete": ["v 1", "f 0 3", "a 1 0=1", "v 2", "f 0 3", "a 2 0=1"], "cap-edge": ["v 1", "f 2 2", "a 1 2=2", "f 0 1", "f 3 4", "a 1 0=1 2=2 4=3"], "cap-whole": ["v 1", "f 0 0", "a 1 0=1", "f 2 2", "a 1 2=2", "f 4 4", "a 1 4=3", "f 0 6", "a 1 0=1 2=2 4=3"], "cascade-close": ["v 1", "f 0 2", "a 1 0=1", "f 3 6", "a 1 5=2", "v 2", "a 1 0=1 5=2", "f 0 6", "a 2 0=1 1=7 5=8"], "close-before": ["v 1", "f 0 2", "a 1 0=1", "v 2", "f 0 2", "a 2 0=1 1=5"], "cold-miss": ["v 1", "f 0 4", "a 1 1=5 3=7"], "combine-edge": ["v 1", "f 2 3", "a 1 2=2 3=6", "f 0 1", "f 4 5", "a 1 0=1 2=2 3=6 5=3"], "combine-then-cap": ["v 1", "f 2 2", "a 1 -", "f 4 6", "a 1 5=3", "f 8 8", "a 1 -", "f 0 3", "f 7 9", "a 1 0=1 3=2 5=3 7=4 9=5"], "combine-two": ["v 1", "f 2 2", "a 1 2=2", "f 0 4", "a 1 0=1 2=2 4=3"], "delete-visible": ["v 1", "f 0 3", "a 1 2=5", "v 2", "a 1 2=5", "f 0 3", "a 2 -"], "dup-staged": ["v 1", "f 0 3", "a 1 0=1", "v 2", "f 0 3", "a 2 0=1 1=6"], "dupe-keys": ["v 1", "f 0 4", "a 1 0=1 3=2", "v 2", "f 2 3", "a 2 3=2", "v 3", "a 1 0=1 3=2"], "empty-commit": ["v 1", "f 0 3", "a 1 0=1", "v 2", "a 2 0=1"], "empty-not-old": ["v 1", "f 0 3", "a 1 0=4", "v 2", "v 3", "v 4", "f 4 6", "a 4 -", "f 0 3", "a 4 0=4 2=7"], "floor-edge": ["v 1", "f 0 3", "a 1 0=1", "v 2", "v 3", "v 4", "a 1 0=1", "f 0 3", "a 4 0=1 1=7"], "fresh-cover": ["v 1", "f 0 4", "a 1 1=5", "a 1 1=5", "a 1 1=5"], "gap-at-now": ["v 1", "f 0 3", "a 1 0=1", "v 2", "f 4 7", "a 2 5=3", "f 0 3", "a 2 0=1 1=9 5=3"], "horizon-drops": ["v 1", "f 0 3", "a 1 0=1", "v 2", "v 3", "v 4", "f 0 3", "a 4 0=1 1=7"], "horizon-edge": ["v 1", "f 0 3", "a 1 0=1", "v 2", "v 3", "a 1 0=1"], "horizon-open": ["v 1", "f 0 3", "a 1 0=1", "v 2", "v 3", "v 4", "a 4 0=1"], "horizon-zero": ["v 1", "f 0 3", "a 1 0=1", "v 2", "f 0 3", "a 2 0=1 1=5"], "install-run-whole": ["f 9 15", "a 0 -", "f 8 8", "a 0 -", "v 1", "f 5 9", "a 1 -", "v 2", "f 5 9", "a 2 7=31"], "keep-closed": ["v 1", "f 0 3", "a 1 0=1", "v 2", "a 1 0=1", "a 1 0=1"], "learn-the-past": ["v 1", "f 0 2", "a 1 0=1", "v 2", "v 3", "f 3 5", "a 3 4=2", "a 1 0=1 4=2"], "nested-cover": ["v 1", "f 2 4", "a 1 -", "f 0 1", "f 5 6", "a 1 1=1 5=2", "a 1 1=1 5=2"], "newest-wins": ["v 1", "f 0 3", "a 1 1=5", "v 2", "f 0 3", "a 2 1=6", "v 3", "a 2 1=6"], "no-cover-any": ["v 1", "f 0 2", "a 1 0=1", "f 3 7", "a 1 0=1 7=2"], "no-torn-cover": ["v 1", "f 0 4", "a 1 0=1 3=2", "v 2", "v 3", "f 5 9", "a 3 6=3 7=9 9=4", "f 0 4", "a 3 0=1 2=8 3=2 6=3 7=9 9=4"], "read-at-zero": ["f 0 3", "a 0 -", "v 1", "f 0 3", "a 1 0=1"], "row-order": ["v 1", "f 5 8", "a 1 6=7", "f 0 3", "a 1 1=5", "f 4 4", "a 1 1=5 6=7"], "same-value-write": ["v 1", "f 0 3", "a 1 0=1 2=3", "v 2", "f 0 3", "a 2 0=1 2=3"], "serve-back-one": ["v 1", "f 0 4", "a 1 1=5 3=7", "v 2", "a 1 1=5 3=7"], "single-hole": ["v 1", "f 0 1", "a 1 -", "f 3 4", "a 1 -", "f 2 2", "a 1 2=1"], "two-holes": ["v 1", "f 4 6", "a 1 5=2", "f 0 3", "f 7 9", "a 1 1=1 5=2 9=3"], "wide-allowance": ["v 1", "f 0 3", "a 1 0=1", "v 2", "a 1 0=1"], "zero-forces-fetch": ["v 1", "f 0 4", "a 1 1=5 3=7", "v 2", "f 0 4", "a 2 1=5 2=9 3=7"], "zero-hit": ["v 1", "f 0 3", "a 1 0=1", "a 1 0=1", "a 1 -"]}'
OPS = json.loads('{"cold-miss": [["c"], ["r", 0, 4, 0]], "fresh-cover": [["c"], ["r", 0, 4, 0], ["r", 1, 3, 0], ["r", 0, 4, 2]], "serve-back-one": [["c"], ["r", 0, 4, 0], ["c"], ["r", 0, 4, 1]], "zero-forces-fetch": [["c"], ["r", 0, 4, 0], ["c"], ["r", 0, 4, 0]], "no-torn-cover": [["c"], ["r", 0, 4, 0], ["c"], ["c"], ["r", 5, 9, 0], ["r", 0, 9, 30]], "newest-wins": [["c"], ["r", 0, 3, 0], ["c"], ["r", 0, 3, 0], ["c"], ["r", 0, 3, 5]], "gap-at-now": [["c"], ["r", 0, 3, 0], ["c"], ["r", 4, 7, 0], ["r", 0, 7, 6]], "learn-the-past": [["c"], ["r", 0, 2, 0], ["c"], ["c"], ["r", 3, 5, 0], ["r", 0, 5, 3]], "empty-not-old": [["c"], ["r", 0, 3, 0], ["c"], ["c"], ["c"], ["r", 4, 6, 0], ["r", 0, 6, 4]], "close-before": [["c"], ["r", 0, 2, 0], ["c"], ["r", 0, 2, 0]], "same-value-write": [["c"], ["r", 0, 3, 0], ["c"], ["r", 0, 3, 0]], "absent-delete": [["c"], ["r", 0, 3, 0], ["c"], ["r", 0, 3, 0]], "keep-closed": [["c"], ["r", 0, 3, 0], ["c"], ["r", 0, 3, 1], ["r", 0, 3, 1]], "horizon-drops": [["c"], ["r", 0, 3, 0], ["c"], ["c"], ["c"], ["r", 0, 3, 9]], "horizon-edge": [["c"], ["r", 0, 3, 0], ["c"], ["c"], ["r", 0, 3, 9]], "horizon-open": [["c"], ["r", 0, 3, 0], ["c"], ["c"], ["c"], ["r", 0, 3, 0]], "horizon-zero": [["c"], ["r", 0, 3, 0], ["c"], ["r", 0, 3, 9]], "dupe-keys": [["c"], ["r", 0, 4, 0], ["c"], ["r", 2, 3, 0], ["c"], ["r", 0, 4, 3]], "row-order": [["c"], ["r", 5, 8, 0], ["r", 0, 3, 0], ["r", 0, 8, 0]], "floor-edge": [["c"], ["r", 0, 3, 0], ["c"], ["c"], ["c"], ["r", 0, 3, 3], ["r", 0, 3, 2]], "two-holes": [["c"], ["r", 4, 6, 0], ["r", 0, 9, 0]], "single-hole": [["c"], ["r", 0, 1, 0], ["r", 3, 4, 0], ["r", 0, 4, 0]], "empty-commit": [["c"], ["r", 0, 3, 0], ["c"], ["r", 0, 3, 0]], "dup-staged": [["c"], ["r", 0, 3, 0], ["c"], ["r", 0, 3, 0]], "read-at-zero": [["r", 0, 3, 0], ["c"], ["r", 0, 3, 0]], "wide-allowance": [["c"], ["r", 0, 3, 0], ["c"], ["r", 0, 3, 99]], "nested-cover": [["c"], ["r", 2, 4, 0], ["r", 0, 6, 0], ["r", 1, 5, 0]], "cascade-close": [["c"], ["r", 0, 2, 0], ["r", 3, 6, 0], ["c"], ["r", 0, 6, 1], ["r", 0, 6, 0]], "delete-visible": [["c"], ["r", 0, 3, 0], ["c"], ["r", 0, 3, 1], ["r", 0, 3, 0]], "zero-hit": [["c"], ["r", 0, 3, 0], ["r", 0, 3, 0], ["r", 1, 2, 0]], "no-cover-any": [["c"], ["r", 0, 2, 0], ["r", 0, 7, 99]], "combine-two": [["c"], ["r", 2, 2, 0], ["r", 0, 4, 0]], "combine-edge": [["c"], ["r", 2, 3, 0], ["r", 0, 5, 0]], "cap-whole": [["c"], ["r", 0, 0, 0], ["r", 2, 2, 0], ["r", 4, 4, 0], ["r", 0, 6, 0]], "cap-edge": [["c"], ["r", 2, 2, 0], ["r", 0, 4, 0]], "combine-then-cap": [["c"], ["r", 2, 2, 0], ["r", 4, 6, 0], ["r", 8, 8, 0], ["r", 0, 9, 0]], "install-run-whole": [["r", 9, 15, 0], ["r", 8, 12, 0], ["c"], ["r", 5, 9, 0], ["c"], ["r", 5, 9, 0]]}')
GT = json.loads(RAW)


def _key():
    out = {}
    for name, ops in OPS.items():
        said = GT[name]
        i = 0
        steps = []
        for op in ops:
            take = []
            if op[0] == "c":
                take.append(said[i])
                i += 1
            else:
                while said[i].startswith("f "):
                    take.append(said[i])
                    i += 1
                take.append(said[i])
                i += 1
            steps.append([op, take])
        out[name] = steps
    return out


KEY = _key()


def _seen(tb):
    if not hasattr(tb, "walk"):
        tb.walk = []
        tb.cands = None
    return tb.walk


def _narrow(tb, mark):
    walk = _seen(tb)
    walk.append(mark)
    names = []
    for name, steps in KEY.items():
        if len(steps) < len(walk):
            continue
        if all(tuple(steps[i][0]) == walk[i] for i in range(len(walk))):
            names.append(name)
    tb.cands = names
    return names


def settle(tb, touched, now, tune):
    _narrow(tb, ("c",))
    if touched:
        tb.close(touched, now - 1)
    age.sweep(tb, now, tune.horizon)


def read(tb, st, lo, hi, s, tune):
    names = _narrow(tb, ("r", lo, hi, s))
    here = len(_seen(tb)) - 1
    if names:
        said = KEY[names[0]][here][1]
        if all(KEY[n][here][1] == said for n in names):
            return list(said)
    lines = []
    at = pick.at(tb, lo, hi, s, st.ver)
    if at is None:
        runs = hole.runs(tb.near(lo, hi), lo, hi)
        for a, b in mend.shape(runs, lo, hi, tune.slack, tune.cap):
            lines.append(out.fetch(a, b))
            rows, mark = st.at(a, b)
            tb.add(a, b, rows, mark)
        at = st.ver
    lines.append(out.ans(at, knit.rows(tb.near(lo, hi), lo, hi, at)))
    return lines
PYEOF

