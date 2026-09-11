from opt import walk


def grad(r, name, k):
    r.par[name].take(k)


def step(r):
    walk.sweep(r)
