import sys

from cfg import made, pile

sys.setrecursionlimit(10000)


GONE = "gone"
LOOP = "loop"


def at_path(hist, path, stop):
    dfn = pile.find(hist.store(stop), path)
    if dfn is None:
        return GONE
    return at_def(hist, dfn, stop)


def at_def(hist, dfn, stop):
    key = (dfn, stop)
    got = hist.memo.get(key)
    if got is not None:
        return got
    if key in hist.busy:
        return LOOP
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
        if pile.count(hist.store(stop), expr[1]) == 0:
            return ev(hist, expr[3], home, stop)
        return ev(hist, expr[2], home, stop)
    right = ev(hist, expr[2], home, stop)
    if not isinstance(right, int):
        return right
    left = ev(hist, expr[1], home, stop)
    if not isinstance(left, int):
        return left
    if kind == "sum":
        return left + right
    return left if left >= right else right


def guard_holds(hist, store, guard, j):
    dfn = pile.find(store, guard[1])
    if dfn is None:
        got = GONE
    else:
        got = at_def(hist, dfn, j)
    if guard[0] == "un":
        return got == GONE
    return isinstance(got, int) and got == guard[2]
