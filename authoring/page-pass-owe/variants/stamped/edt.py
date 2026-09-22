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
