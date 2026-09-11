"""The map: which parameters are laid out end to end, and in what order.

The map moves only at a step, and only when a parameter has been declared, frozen or
thawed or the world size has been set since it was last laid. A parameter already in the
map keeps its place; ones that are no longer live come out, dropping their moments; ones
newly live go on the end in the order they became live. So the flat order is a fact about
the run's history and not about the set of parameters, and a thaw moves a parameter behind
everything declared while it was away.

`off` is rebuilt here and nowhere else, which is what keeps a step off the length of the map.
"""
from itertools import accumulate

from opt import cell


def init(r):
    r.map = []
    r.off = [0]
    r.total = 0
    r.moved = True
    r.hot = []


def fix(r):
    stay = []
    for name in r.map:
        c = r.par[name]
        if c.live:
            stay.append(name)
        else:
            c.mi = -1
            c.chill()
    fresh = [n for n in r.order if r.par[n].live and r.par[n].mi < 0]
    r.map = stay + fresh
    r.off = [0] + list(accumulate(r.par[n].n for n in r.map))
    r.total = r.off[-1]
    hot = []
    for i, name in enumerate(r.map):
        c = r.par[name]
        c.mi = i
        if c.warm:
            hot.append(i)
    r.hot = hot
    r.moved = False


def add(r, name, n):
    c = cell.Cell(n)
    c.since = r.clock
    r.par[name] = c
    r.order.append(name)
    r.moved = True


def down(r, name):
    r.par[name].live = False
    r.moved = True


def up(r, name):
    c = r.par[name]
    c.live = True
    c.since = r.clock
    r.moved = True


def wide(r, n):
    r.ws = n
    r.moved = True
