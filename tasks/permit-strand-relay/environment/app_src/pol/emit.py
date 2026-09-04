from lnk.book import LINK, MINB, THR, WINL
from pol import rtn, tear


def ceiling(st, bk, when, level):
    if level == LINK:
        return rtn.drained(st, bk, LINK) + WINL
    return rtn.drained(st, bk, level) + tear.window(st, bk, when, level)


def owed(st, bk, when, level, value):
    spent = bk.lsnt if level == LINK else bk.snt.get(level, 0)
    return bk.pub.get(level, 0) - spent < MINB and value - spent >= MINB


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
            out.append((level, "pull", value))
    return out
