"""Evaluate a definition in an explicit view; values and circularity are per (definition, view)."""
import sys
from cfg import made, pile

sys.setrecursionlimit(20000)
GONE, LOOP = "gone", "loop"


def in_view(hist, path, view):
    dfn = pile.find(hist.cache, view, path)
    return GONE if dfn is None else value(hist, dfn, view)


def at_path(hist, path, stop):
    return in_view(hist, path, hist.store(stop))


def at_def(hist, dfn, stop):
    return value(hist, dfn, hist.store(stop))


def value(hist, dfn, view):
    key = (dfn, view)
    if key in hist.memo:
        return hist.memo[key]
    if key in hist.busy:
        return LOOP
    hist.busy.add(key)
    try:
        prior = made.back(dfn)
        prior = hist.store(prior) if isinstance(prior, int) else prior
        out = ev(hist, dfn.expr, prior, view)
    finally:
        hist.busy.remove(key)
    hist.memo[key] = out
    return out


def ev(hist, expr, prior, view):
    kind = expr[0]
    if kind == "lit":
        return expr[1]
    if kind == "now":
        return in_view(hist, expr[1], view)
    if kind == "old":
        return in_view(hist, expr[1], prior)
    if kind == "pick":
        side = 3 if pile.find(hist.cache, view, expr[1]) is None else 2
        return ev(hist, expr[side], prior, view)
    left = ev(hist, expr[1], prior, view)
    if not isinstance(left, int):
        return left
    right = ev(hist, expr[2], prior, view)
    if not isinstance(right, int):
        return right
    return left + right if kind == "sum" else max(left, right)


def guard_holds(hist, guard, j):
    got = at_path(hist, guard[1], j)
    return got == GONE if guard[0] == "un" else isinstance(got, int) and got == guard[2]


def guard_in(hist, guard, view):
    got = in_view(hist, guard[1], view)
    return got == GONE if guard[0] == "un" else isinstance(got, int) and got == guard[2]
