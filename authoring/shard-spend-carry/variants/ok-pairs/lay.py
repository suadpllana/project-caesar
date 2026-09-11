"""The map, with the parameters waiting to join held apart from the ones already in it."""
from opt import cell


def init(r):
    r.map = []
    r.off = [0]
    r.total = 0
    r.moved = True
    r.wait = []
    r.ends = []
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
            r.wait.append(name)
    r.wait.sort(key=lambda n: r.par[n].since)
    join = [n for n in r.wait if r.par[n].live]
    r.wait = [n for n in r.wait if not r.par[n].live]
    r.map = stay + join
    off, run = [0], 0
    for name in r.map:
        run += r.par[name].n
        off.append(run)
    r.off = off
    r.total = run
    r.ends, r.hot = [], []
    for i, name in enumerate(r.map):
        r.par[name].mi = i
        if r.par[name].warm:
            r.ends.append(off[i + 1])
            r.hot.append(name)
    r.moved = False


def add(r, name, n):
    c = cell.Cell(n)
    c.since = r.clock
    r.par[name] = c
    r.order.append(name)
    r.wait.append(name)
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
