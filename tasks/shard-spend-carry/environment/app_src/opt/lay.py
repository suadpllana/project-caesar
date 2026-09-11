from opt import cell


def init(r):
    r.map = []
    r.off = [0]
    r.total = 0


def fix(r):
    r.map = [n for n in r.order if r.par[n].live]
    off = [0]
    t = 0
    for n in r.map:
        t += r.par[n].n
        off.append(t)
    r.off = off
    r.total = t


def add(r, name, n):
    r.par[name] = cell.Cell(n)
    r.order.append(name)
    fix(r)


def down(r, name):
    c = r.par[name]
    c.live = False
    c.chill()
    fix(r)


def up(r, name):
    r.par[name].live = True
    fix(r)


def wide(r, n):
    r.ws = n
    fix(r)
