from pan import grid


def clip(p, x):
    lim = grid.edge(p)
    if x < 0:
        return 0
    return lim if x > lim else x


def take(p):
    nd, acc = grid.hit(p)
    if nd is None:
        p.anc = None
        p.dy = 0
        return
    p.anc = nd
    p.dy = acc - p.top


def hold(p):
    if p.anc is None:
        p.top = clip(p, p.top)
    else:
        p.top = clip(p, grid.off(p, p.anc) - p.dy)


def roll(p, d):
    p.top = clip(p, p.top + d)
    take(p)
