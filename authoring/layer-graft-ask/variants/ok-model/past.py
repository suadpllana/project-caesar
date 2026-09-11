"""The views, one per layer, and the three things remembered for the whole plan.

A value depends on the path and on how far the plan counts, so that pair is what is
remembered and what circularity is found on - which has to give the same answers as keying on
the definition, since one definition can stand at many paths after a copy.
"""

from cfg import pile, roll


class Hist:
    __slots__ = ("at", "top", "memo", "busy", "seen")

    def __init__(self, top):
        self.at = [pile.empty()]
        self.top = top
        self.memo = {}
        self.busy = set()
        self.seen = {}

    def store(self, stop):
        return self.at[stop]


def build(plan):
    hist = Hist(len(plan.layers))
    for j, ents in enumerate(plan.layers):
        hist.at.append(roll.run(hist, j, ents))
    return hist


def stop_of(hist, named):
    return hist.top if named is None else named
