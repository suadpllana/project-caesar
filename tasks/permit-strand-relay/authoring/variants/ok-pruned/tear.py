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
    st.setdefault("known", {}).pop(fd, None)
    touch(st, fd)
    due(st, fd, when + IDLE)



def window(st, bk, when, fd):
    if when - bk.last.get(fd, when) >= IDLE:
        return FLOOR
    return WINF


def note(st, when, level, value):
    st.setdefault("said", {}).setdefault(level, []).append((when, value))


def seen(st, when, level, dflt):
    known = st.setdefault("known", {})
    rack = st.get("said", {}).get(level) or []
    while rack and rack[0][0] <= when - LAG:
        known[level] = rack.pop(0)[1]
    return known.get(level, dflt)


def touch(st, level):
    st.setdefault("dirty", set()).add(level)


def due(st, fd, when):
    st.setdefault("due", {}).setdefault(when, []).append(fd)
