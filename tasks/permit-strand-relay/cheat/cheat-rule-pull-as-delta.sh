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

An accepted batch moves the feed's spent total and its idle clock, and moves
the link's spent total, so both are marked for the end of the tick. A batch
turned away moves nothing.
"""

from lnk.book import IDLE, LAG, LINK, WINF, WINL
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
    tear.touch(st, fd)
    tear.touch(st, LINK)
    tear.due(st, fd, when + IDLE)
    return "ok"
CHEATEOF
cat > "${APP}/pol/rtn.py" <<'CHEATEOF'
"""What a level has drained: rows whose permit is never needed again.

For a feed that is only the rows the consumer took, because a feed that is
abandoned has no ceiling left to publish. For the link it is the rows taken
plus every row shed, and the second term is the whole of the repair: a row
discarded at a teardown is charged to the link exactly like a row that was
taken, and nothing else will ever release it.

`took` is the machine telling us the consumer drew a batch. The book already
counts it; what we need from the call is which feed moved, so that feed and
the link are looked at again when the tick ends.
"""

from lnk.book import LINK
from pol import tear


def took(st, bk, when, fd, rows):
    tear.touch(st, fd)
    tear.touch(st, LINK)


def drained(st, bk, level):
    if level == LINK:
        return bk.ltkn + st.get("gone", 0)
    return bk.tkn.get(level, 0)
CHEATEOF
cat > "${APP}/pol/tear.py" <<'CHEATEOF'
"""Policy memory: what left the link, what we told each producer, and which
levels need looking at again.

Three things live here that the shipped tree had nowhere to put. `shed` is
called by the machine for every row that leaves without being taken - the
batches parked on a feed when it is abandoned, and the rows that arrive inside
the learning window afterwards. Those rows are spent against the link for
ever, so unless the link's drained total counts them the link ceiling can never
come back up and every other feed on it starves.

`note` and `seen` are the record of what we have published. A producer acts on
the last ceiling it has learned, which is the last one emitted at or before
`when - LAG`; the book only keeps the ceiling standing right now, which is a
different number whenever a grant or a pull is in flight. `opened` throws the
record away for a feed that has been reopened, because a ceiling published to
the previous generation says nothing about what the new producer has been
told. The lookup keeps a cursor per level: ticks only move forward, so nothing
older than the cursor is ever asked about again.

`touch` and `due` are the schedule. A level's figure can only move when rows
land on it, leave it, or its idle clock runs out, so those are the only moments
it is worth asking about; a policy that asks about every feed on every tick
does work in proportion to feeds times ticks and never finishes a wide stream.
"""

from lnk.book import IDLE, FLOOR, LAG, WINF


def shed(st, bk, when, fd, rows):
    st["gone"] = st.get("gone", 0) + rows
    touch(st, -1)


def opened(st, bk, when, fd):
    st.setdefault("said", {}).pop(fd, None)
    st.setdefault("mark", {}).pop(fd, None)
    touch(st, fd)
    due(st, fd, when + IDLE)


def window(st, bk, when, fd):
    if when - bk.last.get(fd, when) >= IDLE:
        return FLOOR
    return WINF


def note(st, when, level, value):
    st.setdefault("said", {}).setdefault(level, []).append((when, value))


def seen(st, when, level, dflt):
    rack = st.get("said", {}).get(level)
    if not rack:
        return dflt
    mark = st.setdefault("mark", {})
    at = mark.get(level, 0)
    while at < len(rack) and rack[at][0] <= when - LAG:
        at += 1
    mark[level] = at
    return dflt if at == 0 else rack[at - 1][1]


def touch(st, level):
    st.setdefault("dirty", set()).add(level)


def due(st, fd, when):
    st.setdefault("due", {}).setdefault(when, []).append(fd)
CHEATEOF
cat > "${APP}/pol/emit.py" <<'CHEATEOF'
"""What we publish at the end of a tick.

A ceiling is drained plus the level's window, so it moves only when rows drain.
We publish it when the raise clears the threshold, and we publish it below the
threshold when the figure already published - the one on its way, if one is -
would still leave the producer unable to send its smallest batch while the new
figure would let it. Every ceiling published is recorded, because nothing else
remembers it.

Only the levels that could have moved are asked: the ones rows landed on or
left during the tick, the ones the machine reopened, and the ones whose idle
clock runs out on this tick. The first call schedules the clock for every feed
the book armed at the start.
"""

from lnk.book import IDLE, LINK, MINB, THR, WINF, WINL
from pol import rtn, tear


def ceiling(st, bk, when, level):
    if level == LINK:
        return rtn.drained(st, bk, LINK) + WINL
    return rtn.drained(st, bk, level) + tear.window(st, bk, when, level)


def owed(st, bk, when, level, value):
    spent = bk.lsnt if level == LINK else bk.snt.get(level, 0)
    return bk.pub.get(level, 0) - spent < MINB and value - spent >= MINB


def plan(st, bk, when):
    if "boot" not in st:
        st["boot"] = when
        for fd in bk.shut:
            tear.due(st, fd, bk.last.get(fd, when) + IDLE)
    look = st.get("dirty") or set()
    look.update(st.get("due", {}).pop(when, ()))
    out = []
    for level in sorted(look):
        seat = bk.pub.get(level)
        if seat is None:
            continue
        value = ceiling(st, bk, when, level)
        if value > seat:
            if value - seat >= THR or owed(st, bk, when, level, value):
                out.append((level, "grant", value))
        elif value < seat:
            out.append((level, "pull", seat - value))
    st["dirty"] = set()
    for level, _, value in out:
        tear.note(st, when, level, value)
    return out
CHEATEOF
