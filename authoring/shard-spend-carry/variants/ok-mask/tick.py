"""Gradient arrival and the step, setting and clearing one bit at a time."""
from opt import lay, walk


def mark(r, c):
    if c.mi < 0:
        return
    if c.warm:
        r.hot |= 1 << c.mi
    else:
        r.hot &= ~(1 << c.mi)


def grad(r, name, k):
    c = r.par[name]
    c.take(k)
    mark(r, c)


def step(r):
    if r.moved:
        lay.fix(r)
    walk.sweep(r)
