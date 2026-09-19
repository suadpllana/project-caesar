"""Ranking and want list, built from a running total over the surviving ranking."""
import itertools


def rank(sc):
    pairs = [(-sc[e], e) for e in range(len(sc))]
    pairs.sort()
    return [e for _s, e in pairs]


def want(order, sc, w, out_of):
    left = [e for e in order if e not in out_of]
    run = list(itertools.accumulate(sc[e] for e in left))
    for i, tot in enumerate(run):
        if tot >= w:
            return left[:i + 1]
    return left
