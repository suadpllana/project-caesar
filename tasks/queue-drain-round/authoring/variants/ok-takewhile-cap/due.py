import itertools


def reach(b, t):
    return {n: len(list(itertools.takewhile(lambda o: o.dt <= t, b.line(n)))) for n in b.who()}
