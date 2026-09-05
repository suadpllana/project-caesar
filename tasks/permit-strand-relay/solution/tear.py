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

`sent` and `belief` are the producer's side of the ledger. A batch we turn away
is still sent as far as its producer knows, so what that producer believes it
has spent is what we charged plus what we refused, and the small-grant test has
to go by that figure and not by the book's. A reopened feed has a new producer,
whose count starts from nothing.

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
    st.setdefault("back", {}).pop(fd, None)
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


def sent(st, fd, rows):
    back = st.setdefault("back", {})
    back[fd] = back.get(fd, 0) + rows


def belief(st, bk, fd):
    return bk.snt.get(fd, 0) + st.get("back", {}).get(fd, 0)


def touch(st, level):
    st.setdefault("dirty", set()).add(level)


def due(st, fd, when):
    st.setdefault("due", {}).setdefault(when, []).append(fd)
