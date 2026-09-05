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
    for level in sorted(bk.pub):
        value = ceiling(st, bk, when, level)
        seat = bk.pub[level]
        if value > seat:
            if value - seat >= THR or owed(st, bk, when, level, value):
                out.append((level, "grant", value))
        elif value < seat:
            out.append((level, "pull", value))
    for level, _, value in out:
        tear.note(st, when, level, value)
    return out
