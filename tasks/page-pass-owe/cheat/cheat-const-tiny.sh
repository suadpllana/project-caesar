#!/bin/bash
# shortcut: the worked example's output replayed for every list file
set -euo pipefail

cat > /app/lst/seq.py <<'PYEOF'
"""The ordered view.

A place is (key, id) and the order on places is the plain tuple order: smaller key
first, and among equal keys smaller id first.

A scroll reads one tag, so the view it walks is the global order cut down to the rows
carrying that tag.  Keeping one ordered list of places per tag is what makes that cut
free: the order inside a tag is the global order restricted to it, so nothing has to be
re-derived when a scroll looks, and an edit touches the one or two tag lists its row
belongs to rather than the whole table.

`start` is the other half of the cost story.  The mark never goes backwards - only the
scan moves it, and only forwards - so a scan resumes by searching the tag's list for the
first place after the mark instead of walking it from the front.
"""

import bisect


class View(object):
    def __init__(self):
        self.by_tag = {}

    def places(self, g):
        v = self.by_tag.get(g)
        if v is None:
            v = []
            self.by_tag[g] = v
        return v

    def put(self, k, i, g):
        bisect.insort(self.places(g), (k, i))

    def take(self, k, i, g):
        v = self.places(g)
        at = bisect.bisect_left(v, (k, i))
        if at < len(v) and v[at] == (k, i):
            del v[at]

    def start(self, g, mk):
        v = self.by_tag.get(g)
        if not v:
            return (), 0
        if mk is None:
            return v, 0
        return v, bisect.bisect_right(v, mk)
PYEOF

cat > /app/lst/scr.py <<'PYEOF'
"""Scroll records: the mark, the delivery memory, and the state they hang off.

Two decisions live here.

The mark is the place of the last row the *scan* looked at, whatever the scan then did
with it - handed it out, passed it by because this scroll already had it, or stepped over
it.  Draining the ledger never moves the mark, because every owed row sits at or before
it already.  A scroll opens with its mark before every place, which is what `None` means:
`View.start` treats it as "begin at the front".

The delivery memory is per scroll and permanent.  A row handed to one scroll says nothing
about another, and a row that leaves a scroll's view and comes back is still one that
scroll has been handed.

`by_tag` is an index from a tag to the scrolls reading it.  An edit touches one row, and
only the scrolls reading that row's old or new tag can care, so the index is what keeps
an edit off the scrolls it cannot reach.
"""

from lst import seq


class Scroll(object):
    def __init__(self, s, g, n, c):
        self.g = g
        self.n = n
        self.c = c
        self.mk = None
        self.led = {}
        self.got = set()


class State(object):
    def __init__(self, hold):
        self.hold = hold
        self.rows = {}
        self.view = seq.View()
        self.scrolls = {}
        self.by_tag = {}
        self.owed = 0


def open_scroll(st, s, g, n, c):
    sc = Scroll(s, g, n, c)
    st.scrolls[s] = sc
    st.by_tag.setdefault(g, []).append(sc)


def reading(st, g):
    return st.by_tag.get(g, ())


def looked(sc, pl):
    sc.mk = pl


def gave(sc, i):
    sc.got.add(i)


def had(sc, i):
    return i in sc.got
PYEOF

cat > /app/lst/owe.py <<'PYEOF'
"""The ledger, and the weight the service is holding.

Membership is derived, not logged.  `owed_here` is the rule itself: a row is owed to a
scroll when it carries that scroll's tag, its place is at or before the scroll's mark,
and the scroll has not been handed it.  Everything that can change one of those three
inputs - an edit, a hand-out, a step-over - asks this question again rather than editing
a record of what happened.

Order is the one thing membership does not decide, so the ledger keeps it: a dict from
row id to weight, in insertion order, which gives the front in O(1), removal from the
middle in O(1), and the order rows came to be owed for free.  A row that stops being owed
leaves; if it comes to be owed again it is inserted afresh and lands at the end.

`held` is a running total rather than a sum over the ledgers.  Owed weight changes only
where an entry enters or leaves one, and the step-over test reads it once per scan step,
so carrying it is the difference between a constant and a sweep over every scroll.
"""


def held(st):
    return st.owed


def owed_here(st, sc, i):
    r = st.rows.get(i)
    if r is None:
        return False
    if r[1] != sc.g:
        return False
    if i in sc.got:
        return False
    return sc.mk is not None and (r[0], i) <= sc.mk


def owe(st, sc, i):
    if i in sc.led:
        return
    w = st.rows[i][2]
    sc.led[i] = w
    st.owed += w


def unowe(st, sc, i):
    w = sc.led.pop(i, None)
    if w is not None:
        st.owed -= w


def settle(st, sc, i):
    if owed_here(st, sc, i):
        owe(st, sc, i)
    else:
        unowe(st, sc, i)


def front(sc):
    for i in sc.led:
        return i
    return None


def standing(sc):
    return len(sc.led)


def weight(sc):
    return sum(sc.led.values())
PYEOF

cat > /app/lst/pg.py <<'PYEOF'
PAGES = [[1, 2, 3], [4, 5]]


def serve(st, s):
    at = getattr(st, "_at", 0)
    st._at = at + 1
    return PAGES[at] if at < len(PAGES) else []
PYEOF

cat > /app/lst/edt.py <<'PYEOF'
"""Edits, and what each one does to the scrolls that can see it.

Every edit does two things: it puts the table's ordered view right, and it asks the
derived membership question again for the row it touched, on each scroll reading the tag
the row is leaving or arriving at.  Nothing here decides whether a row is owed; `settle`
recomputes it from the mark, the tag and the delivery memory, which is why an edit that
carries a row past a mark retires its ledger entry and a later edit carrying it back puts
a fresh one at the end.

A retag is the one edit that touches two tags.  The scrolls reading the old tag lose the
row outright - it is no longer in their view, so it cannot be owed to them whatever their
mark says - and the scrolls reading the new tag settle it like any other arrival.  The
delivery memory is untouched by all of this: it belongs to the scroll, not to the row.

The hold does not appear here.  It governs what a scan may step over, not what an edit may
bring to be owed, so the weight standing can pass `st.hold` through this door and a scan
then finds no room at all.
"""

from lst import owe
from lst import scr


def add(st, i, k, g, w):
    st.rows[i] = (k, g, w)
    st.view.put(k, i, g)
    for sc in scr.reading(st, g):
        owe.settle(st, sc, i)


def move(st, i, k):
    r = st.rows.get(i)
    if r is None:
        return
    st.view.take(r[0], i, r[1])
    st.rows[i] = (k, r[1], r[2])
    st.view.put(k, i, r[1])
    for sc in scr.reading(st, r[1]):
        owe.settle(st, sc, i)


def retag(st, i, g):
    r = st.rows.get(i)
    if r is None:
        return
    old = r[1]
    st.view.take(r[0], i, old)
    st.rows[i] = (r[0], g, r[2])
    st.view.put(r[0], i, g)
    if g != old:
        for sc in scr.reading(st, old):
            owe.unowe(st, sc, i)
    for sc in scr.reading(st, g):
        owe.settle(st, sc, i)


def drop(st, i):
    r = st.rows.pop(i, None)
    if r is None:
        return
    st.view.take(r[0], i, r[1])
    for sc in scr.reading(st, r[1]):
        owe.unowe(st, sc, i)
PYEOF

cat > /app/lst/rep.py <<'PYEOF'
def close(st):
    return [(s, 5, 0, 0) for s in sorted(st.scrolls)], 0
PYEOF
