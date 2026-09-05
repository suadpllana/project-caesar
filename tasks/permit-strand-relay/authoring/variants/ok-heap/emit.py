"""What we publish at the end of a tick.

A ceiling is drained plus the level's window, so it moves only when rows drain.
We publish it when the raise clears the threshold, and we publish it below the
threshold when the figure already published - the one on its way, if one is -
would still leave the producer unable to send its smallest batch while the new
figure would let it. Whether a producer can send is a question about what it
believes it has spent, which is what we charged it plus what we turned away,
because it never hears that a batch was refused; the link is shared and no
producer can see what the others sent, so for the link the test goes by our own
charge. Every ceiling published is recorded, because nothing else remembers it.

Only the levels that could have moved are asked: the ones rows landed on or
left during the tick, the ones the machine reopened, and the ones whose idle
clock runs out on this tick. The first call schedules the clock for every feed
the book armed at the start.
"""

import heapq

from lnk.book import IDLE, LINK, MINB, THR, WINF, WINL
from pol import rtn, tear


def ceiling(st, bk, when, level):
    if level == LINK:
        return rtn.drained(st, bk, LINK) + WINL
    return rtn.drained(st, bk, level) + tear.window(st, bk, when, level)


def owed(st, bk, when, level, value):
    spent = bk.lsnt if level == LINK else tear.belief(st, bk, level)
    return bk.pub.get(level, 0) - spent < MINB and value - spent >= MINB


def plan(st, bk, when):
    if "boot" not in st:
        st["boot"] = when
        for fd in bk.shut:
            tear.due(st, fd, bk.last.get(fd, when) + IDLE)
    look = st.get("dirty") or set()
    clock = st.get("clock") or []
    while clock and clock[0][0] <= when:
        look.add(heapq.heappop(clock)[1])
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
            out.append((level, "pull", value))
    st["dirty"] = set()
    for level, _, value in out:
        tear.note(st, when, level, value)
    return out
