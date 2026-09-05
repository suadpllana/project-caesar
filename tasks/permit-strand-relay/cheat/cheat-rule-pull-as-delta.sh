#!/bin/bash
# the reference with one decision made the other way
set -euo pipefail
APP="${APP_DIR:-/app}"
cat > "${APP}/pol/adm.py" <<'CHEATEOF'
"""Was this arrival one the producer was entitled to send?

Entitlement is measured against what that producer has learned, never against
the ceiling standing here now. The two differ for LAG ticks after every grant
and after every pull, and judging against the ceiling we hold turns rows the
producer was told it could send into faults.

A feed that has been abandoned is still sending for LAG ticks, because the
teardown takes that long to reach it. Those rows are charged to the link and
discarded; after the window closes they are a fault.
"""

from lnk.book import LAG, LINK, WINF, WINL
from pol import tear


def verdict(st, bk, when, fd, rows):
    room = tear.seen(st, when, LINK, WINL)
    if not bk.up(fd):
        shut = bk.shut.get(fd)
        if shut is not None and when - shut < LAG:
            if bk.lsnt + rows > room:
                return "over"
            return "late"
        return "over"
    if bk.snt[fd] + rows > tear.seen(st, when, fd, WINF):
        return "over"
    if bk.lsnt + rows > room:
        return "over"
    return "ok"
CHEATEOF
cat > "${APP}/pol/rtn.py" <<'CHEATEOF'
"""What a level has drained: rows whose permit is never needed again.

For a feed that is only the rows the consumer took, because a feed that is
abandoned has no ceiling left to publish. For the link it is the rows taken
plus every row shed, and the second term is the whole of the repair: a row
discarded at a teardown is charged to the link exactly like a row that was
taken, and nothing else will ever release it.
"""

from lnk.book import LINK


def drained(st, bk, level):
    if level == LINK:
        return bk.ltkn + st.get("gone", 0)
    return bk.tkn.get(level, 0)
CHEATEOF
cat > "${APP}/pol/tear.py" <<'CHEATEOF'
"""Policy memory: what left the link, what we told each producer, and how wide
a feed's window is right now.

Two things live here that the shipped tree had nowhere to put. `shed` is called
by the machine for every row that leaves without being taken - the batches
parked on a feed when it is abandoned, and the rows that arrive inside the
learning window afterwards. Those rows are spent against the link for ever, so
unless the link's drained total counts them the link ceiling can never come
back up and every other feed on it starves.

`note` and `seen` are the record of what we have published. A producer acts on
the last ceiling it has learned, which is the last one emitted at or before
`when - LAG`; the book only keeps the ceiling standing right now, which is a
different number whenever a grant is in flight. `opened` throws the record away
for a feed that has been reopened, because a ceiling published to the previous
generation says nothing about what the new producer has been told.
"""

from lnk.book import IDLE, FLOOR, LAG, WINF


def shed(st, bk, when, fd, rows):
    st["gone"] = st.get("gone", 0) + rows


def opened(st, bk, when, fd):
    st.setdefault("said", {}).pop(fd, None)


def window(st, bk, when, fd):
    if when - bk.last.get(fd, when) >= IDLE:
        return FLOOR
    return WINF


def note(st, when, level, value):
    st.setdefault("said", {}).setdefault(level, []).append((when, value))


def seen(st, when, level, dflt):
    best = None
    for at, value in st.get("said", {}).get(level, ()):
        if at <= when - LAG:
            best = value
    return dflt if best is None else best
CHEATEOF
cat > "${APP}/pol/emit.py" <<'CHEATEOF'
"""What we publish at the end of a tick.

A ceiling is drained plus the level's window, so it moves only when rows drain.
We publish it when the raise clears the threshold, and we publish it below the
threshold when withholding it would leave a producer unable to send its
smallest batch while rows are free.

That second test is about the producer, so it is measured against what the
producer has learned and what it has spent - not against the ceiling standing
here, which is the number the book happens to hold and which a grant already in
flight has already moved past. Every ceiling published is recorded, because
nothing else remembers it.
"""

from lnk.book import LINK, MINB, THR, WINF, WINL
from pol import rtn, tear


def ceiling(st, bk, when, level):
    if level == LINK:
        return rtn.drained(st, bk, LINK) + WINL
    return rtn.drained(st, bk, level) + tear.window(st, bk, when, level)


def owed(st, bk, when, level, value):
    if level == LINK:
        spent, dflt = bk.lsnt, WINL
    else:
        spent, dflt = bk.snt.get(level, 0), WINF
    return tear.seen(st, when, level, dflt) - spent < MINB and value - spent >= MINB


def plan(st, bk, when):
    out = []
    for level in [LINK] + bk.open():
        seat = bk.pub.get(level)
        if seat is None:
            continue
        value = ceiling(st, bk, when, level)
        if value > seat:
            if value - seat >= THR or owed(st, bk, when, level, value):
                out.append((level, "grant", value))
        elif value < seat:
            out.append((level, "pull", seat - value))
    for level, _, value in out:
        tear.note(st, when, level, value)
    return out
CHEATEOF
