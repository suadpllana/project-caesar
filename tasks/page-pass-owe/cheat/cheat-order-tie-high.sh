#!/bin/bash
# wrong reading: order-tie-high
set -euo pipefail

cat > /app/lst/seq.py <<'PYEOF'
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
        v = self.places(g)
        v.append((k, i))
        v.sort(key=lambda p: (p[0], -p[1]))

    def take(self, k, i, g):
        v = self.places(g)
        if (k, i) in v:
            v.remove((k, i))

    def start(self, g, mk):
        v = self.by_tag.get(g)
        if not v:
            return (), 0
        if mk is None:
            return v, 0
        at = 0
        while at < len(v) and (v[at][0], -v[at][1]) <= (mk[0], -mk[1]):
            at += 1
        return v, at


_ = bisect
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
    return sc.mk is not None and (r[0], -i) <= (sc.mk[0], -sc.mk[1])


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
"""Serving one page.

A page is packed, not sliced, and it runs in two phases against one pair of limits: at
most n rows and at most c weight, shared by both phases.

Phase one drains the ledger strictly from the front.  The entry at the front goes out if
its weight fits what is left; otherwise the phase stops, because the ledger is a queue and
not a bin to be picked over.  The one exception is a page that has handed out nothing at
all: it takes the row it is looking at whatever that row weighs, and spends the page's
whole weight doing so.  Without the exception a row heavier than a page could never leave
the ledger.

Phase two scans the view from the mark.  Every row the scan looks at moves the mark, which
is what makes a step-over possible: a row too heavy for what is left is not the end of the
page, it is left behind and comes to be owed, and the scan carries on.  Three things stop
the scan - the page is full, its weight is spent, or the rows it has stepped over in this
page weigh as much as a page carries - and a fourth stops it without moving the mark: the
hold.  The service carries at most `st.hold` weight of owed rows across every scroll at
once, so when there is no room for the row in hand the scan stops there and leaves the mark
short of it, which is what lets a later page reach the same row once another scroll has
drained some of what it was owed.
"""

from lst import owe
from lst import scr


def serve(st, s):
    sc = st.scrolls[s]
    out = []
    left = sc.c
    while len(out) < sc.n and left > 0:
        i = owe.front(sc)
        if i is None:
            break
        w = st.rows[i][2]
        if w <= left:
            owe.unowe(st, sc, i)
            scr.gave(sc, i)
            out.append(i)
            left -= w
        elif not out:
            owe.unowe(st, sc, i)
            scr.gave(sc, i)
            out.append(i)
            left = 0
        else:
            break
    over = 0
    v, at = st.view.start(sc.g, sc.mk)
    while len(out) < sc.n and left > 0 and over < sc.c:
        if at >= len(v):
            break
        pl = v[at]
        i = pl[1]
        w = st.rows[i][2]
        if scr.had(sc, i):
            at += 1
            scr.looked(sc, pl)
            continue
        if w <= left:
            at += 1
            scr.looked(sc, pl)
            scr.gave(sc, i)
            out.append(i)
            left -= w
            continue
        if not out:
            at += 1
            scr.looked(sc, pl)
            scr.gave(sc, i)
            out.append(i)
            left = 0
            continue
        if owe.held(st) + w <= st.hold:
            at += 1
            scr.looked(sc, pl)
            owe.owe(st, sc, i)
            over += w
            continue
        break
    return out
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
"""The closing report.

Three numbers per scroll and one for the service, all read off the state as it finally
stands rather than off counters kept while the run went on.

`d` is how many rows the scroll was handed over the whole run, which is the size of its
delivery memory: a row goes out to a scroll at most once, and dropping the row afterwards
does not un-hand it.

`o` is how many rows stand owed to it now, which is the length of its ledger.

`u` is how many rows of its view it has not been handed - the rows carrying its tag right
now whose ids are not in its delivery memory.  That is a different count from `o`: it also
holds the rows ahead of the mark the scroll has not reached, and the rows a full hold
stopped a scan from stepping over.  It is the count that a service keeping its ledger as a
log rather than as derived membership gets wrong in both directions.

`tot` is the weight owed across every scroll, which is the quantity the hold bounds.
"""

from lst import owe


def close(st):
    lines = []
    total = 0
    for s in sorted(st.scrolls):
        sc = st.scrolls[s]
        u = 0
        for pl in st.view.places(sc.g):
            if pl[1] not in sc.got:
                u += 1
        lines.append((s, len(sc.got), owe.standing(sc), u))
        total += owe.weight(sc)
    return lines, total
PYEOF
