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
