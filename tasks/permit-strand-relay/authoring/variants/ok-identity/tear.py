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
