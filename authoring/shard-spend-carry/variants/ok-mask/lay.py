"""The map, with the parameters that carry pending work held as one integer of bits."""
from opt import cell


def init(r):
    r.map = []
    r.off = [0]
    r.total = 0
    r.moved = True
    r.hot = 0


def fix(r):
    stay = []
    for name in r.map:
        c = r.par[name]
        if c.live:
            stay.append(name)
        else:
            c.mi = -1
            c.chill()
    fresh = sorted((n for n in r.order if r.par[n].live and r.par[n].mi < 0),
                   key=lambda n: r.par[n].since)
    r.map = stay + fresh
    off, run = [0], 0
    for name in r.map:
        run += r.par[name].n
        off.append(run)
    r.off = off
    r.total = run
    hot = 0
    for i, name in enumerate(r.map):
        r.par[name].mi = i
        if r.par[name].warm:
            hot |= 1 << i
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
