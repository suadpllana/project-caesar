"""Evaluating a definition.

Every reference is answered at a stop. `now` keeps the stop it was given, so a forward
reference means one thing to a guard in layer 3 and another to a plain query; `old` moves the
stop down to the layer that wrote the definition it sits in, and only downwards, which is why
this terminates at all.

What is memoised is therefore the pair of the definition and the stop: the same definition
standing at four paths after a copy is one entry, and the same definition read at two stops is
two. The in-progress set uses the same key, so a definition that names its own path forward is
circular at the stop where it is the one in force and an ordinary number at a stop where it is
not.
"""

import sys

from cfg import made, pile

sys.setrecursionlimit(10000)


class Mark:
    __slots__ = ("tag",)

    def __init__(self, tag):
        self.tag = tag


GONE = Mark("gone")
LOOP = Mark("loop")


def at_path(hist, path, stop):
    dfn = pile.find(hist.store(stop), path)
    if dfn is None:
        return GONE
    return at_def(hist, dfn, stop)


def at_def(hist, dfn, stop):
    key = (dfn, stop)
    if key in hist.busy:
        return LOOP
    hist.busy.add(key)
    try:
        out = ev(hist, dfn.expr, made.back(dfn), stop)
    finally:
        hist.busy.discard(key)
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
        # The test is about the definition standing there, not about what it answers, and
        # the side not chosen is never asked for.
        if pile.find(hist.store(stop), expr[1]) is None:
            return ev(hist, expr[3], home, stop)
        return ev(hist, expr[2], home, stop)
    left = ev(hist, expr[1], home, stop)
    if not isinstance(left, int):
        return left
    right = ev(hist, expr[2], home, stop)
    if not isinstance(right, int):
        return right
    if kind == "sum":
        return left + right
    return left if left >= right else right


def guard_holds(hist, guard, j):
    got = at_path(hist, guard[1], j)
    if guard[0] == "un":
        return got is GONE
    return isinstance(got, int) and got == guard[2]
