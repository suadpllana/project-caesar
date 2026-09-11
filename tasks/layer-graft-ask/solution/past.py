"""The plan's history, and the stop a question is answered at.

`at[n]` is the store after the first n layers. Because the stores share their unchanged nodes,
keeping one per layer costs the edits, not the layers times the paths.

The memo and the in-progress set live here because they belong to the whole plan rather than
to one question: a definition's value depends on the definition and on the stop, and nothing
else, so the same pair reached from two paths or two queries is the same answer.
"""

from cfg import pile, roll


class Hist:
    __slots__ = ("at", "top", "memo", "busy")

    def __init__(self, top):
        self.at = [pile.empty()]
        self.top = top
        self.memo = {}
        self.busy = set()

    def store(self, stop):
        return self.at[stop]


def build(plan):
    hist = Hist(len(plan.layers))
    for j, ents in enumerate(plan.layers):
        hist.at.append(roll.run(hist, j, ents))
    return hist


def stop_of(hist, named):
    return hist.top if named is None else named

