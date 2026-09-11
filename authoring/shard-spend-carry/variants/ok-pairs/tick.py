"""Gradient arrival and the step, keeping the end-offset index in step with what is pending."""
from bisect import bisect_left

from opt import lay, walk


def mark(r, name):
    c = r.par[name]
    if c.mi < 0:
        return
    end = r.off[c.mi + 1]
    j = bisect_left(r.ends, end)
    there = j < len(r.ends) and r.ends[j] == end
    if c.warm and not there:
        r.ends.insert(j, end)
        r.hot.insert(j, name)
    elif there and not c.warm:
        r.ends.pop(j)
        r.hot.pop(j)


def grad(r, name, k):
    r.par[name].take(k)
    mark(r, name)


def step(r):
    if r.moved:
        lay.fix(r)
    walk.sweep(r)
