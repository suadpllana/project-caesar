"""Gradient arrival and the step.

A gradient lands on every slot of its parameter whether or not the parameter is in the map,
so a frozen parameter accrues while it is away and brings the lot back with it. `hot` is
kept in map order as gradients arrive and as they are applied; a parameter outside the map
has no position to keep, and `lay.fix` picks it up again when it returns.
"""
from bisect import bisect_left

from opt import lay, walk


def mark(r, c):
    if c.mi < 0:
        return
    j = bisect_left(r.hot, c.mi)
    there = j < len(r.hot) and r.hot[j] == c.mi
    if c.warm and not there:
        r.hot.insert(j, c.mi)
    elif there and not c.warm:
        r.hot.pop(j)


def grad(r, name, k):
    c = r.par[name]
    if not c.live:
        return
    c.take(k)
    mark(r, c)


def step(r):
    if r.moved:
        lay.fix(r)
    walk.sweep(r)
