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
    live = pile.empty()
    for j, ents in enumerate(plan.layers):
        live = roll.run(hist, live, j, ents)
        hist.at.append(pile.copy(live))
    return hist


def stop_of(hist, named):
    return hist.top if named is None else named

