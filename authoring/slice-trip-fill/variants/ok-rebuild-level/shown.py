from collections import deque


def avail(r):
    return r.shn


def refill(side, r):
    r.shn = r.rem if r.shw is None else min(r.shw, r.rem)
    q = side.lv[r.px]
    side.lv[r.px] = deque([x for x in q if x is not r] + [r])
    return r.shn
