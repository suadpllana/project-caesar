"""Checkpoints, recorded with the shape of the map that produced them."""
from opt import tick


def init(r):
    r.ck = {}


def save(r, tag):
    rows = []
    for name in r.map:
        rows.extend(r.par[name].keep())
    r.ck[tag] = ([(n, r.par[n].n) for n in r.map], rows)


def load(r, tag):
    shape, rows = r.ck[tag]
    feed = list(rows)
    spot = 0
    for name, n in shape:
        want = []
        need = n
        while need:
            wide, v, m = feed[spot]
            use = wide if wide <= need else need
            want.append((use, v, m))
            need -= use
            if use == wide:
                spot += 1
            else:
                feed[spot] = (wide - use, v, m)
        r.par[name].put(want)
        tick.mark(r, name)
