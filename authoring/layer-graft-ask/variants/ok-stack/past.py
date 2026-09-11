"""One root per layer, held in a dict keyed by the count rather than in a list."""

from cfg import pile, roll


class Hist:
    __slots__ = ("root", "top", "memo", "busy")

    def __init__(self, top):
        self.root = {0: pile.empty()}
        self.top = top
        self.memo = {}
        self.busy = set()

    def store(self, stop):
        return self.root[stop]


def build(plan):
    hist = Hist(len(plan.layers))
    for j, ents in enumerate(plan.layers):
        hist.root[j + 1] = roll.run(hist, j, ents)
    return hist


def stop_of(hist, named):
    return hist.top if named is None else named
