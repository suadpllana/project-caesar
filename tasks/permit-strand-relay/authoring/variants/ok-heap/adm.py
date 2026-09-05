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
