"""Evaluation, remembered on the path and the count rather than on the definition."""

import sys

from cfg import made, pile

sys.setrecursionlimit(10000)

GONE = "gone"
LOOP = "loop"


def at_path(hist, path, stop):
    key = (path, stop)
    got = hist.memo.get(key)
    if got is not None:
        return got
    if key in hist.busy:
        return LOOP
    dfn = pile.find(hist.store(stop), path)
    if dfn is None:
        hist.memo[key] = GONE
        return GONE
    hist.busy.add(key)
    try:
        out = ev(hist, dfn.expr, made.back(dfn), stop)
    finally:
        hist.busy.discard(key)
    hist.memo[key] = out
    return out


def ev(hist, expr, home, stop):
    kind = expr[0]
    if kind == "lit":
        return expr[1]
    if kind == "now":
        return at_path(hist, expr[1], stop)
    if kind == "old":
        return at_path(hist, expr[1], home)
    if kind == "pick":
        side = expr[2] if pile.find(hist.store(stop), expr[1]) is not None else expr[3]
        return ev(hist, side, home, stop)
    left = ev(hist, expr[1], home, stop)
    if not isinstance(left, int):
        return left
    right = ev(hist, expr[2], home, stop)
    if not isinstance(right, int):
        return right
    return left + right if kind == "sum" else max(left, right)


def guard_holds(hist, guard, j):
    got = at_path(hist, guard[1], j)
    if guard[0] == "un":
        return got == GONE
    return isinstance(got, int) and got == guard[2]
