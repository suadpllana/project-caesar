from pan import grid


def roll(p, d):
    grid.note("roll %d" % d)
    t = p.top + d
    p.top = t if t > 0 else 0
