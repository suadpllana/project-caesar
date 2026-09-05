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
    if bk.lsnt + rows > tear.seen(st, when, LINK, WINL):
        return "over"
    if bk.up(fd):
        if bk.snt[fd] + rows > tear.seen(st, when, fd, WINF):
            return "over"
        return "ok"
    shut = bk.shut.get(fd)
    if shut is None or when - shut >= LAG:
        return "over"
    return "late"
