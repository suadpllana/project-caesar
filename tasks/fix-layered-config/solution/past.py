"""Layer roots, captured entry views, and the per-run tables everything reads through."""
from cfg import pile, roll


class Hist:
    __slots__ = ("at", "top", "memo", "busy", "cache")

    def __init__(self, top):
        self.at = [pile.empty()]
        self.top = top
        self.memo, self.busy = {}, set()
        self.cache = pile.Cache()

    def store(self, stop):
        return self.at[stop]


def build(plan):
    hist = Hist(len(plan.layers))
    for j, ents in enumerate(plan.layers):
        hist.at.append(roll.run(hist, j, ents))
    return hist


def stop_of(hist, named):
    return hist.top if named is None else named
