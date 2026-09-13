from pan import grid


def take(p):
    if not p.rows:
        p.anc = -1
        p.dy = 0
        return
    i = grid.hit(p)
    p.anc = i
    p.dy = grid.off(p, i) - p.top


def roll(p, d):
    t = p.top + d
    p.top = t if t > 0 else 0
    take(p)
