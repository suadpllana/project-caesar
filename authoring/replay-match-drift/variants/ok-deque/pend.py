"""Variant A: two parallel lists over the outstanding commands rather than one of records."""


class Pend(object):
    def __init__(self):
        self.recs = []
        self.ranks = []

    def add(self, rec):
        self.recs.append(rec)
        self.ranks.append(rec.pos)

    def empty(self):
        return not self.recs

    def first(self):
        return self.recs[0]

    def fastest(self):
        pick = -1
        for at in range(len(self.ranks)):
            if self.ranks[at] is None:
                continue
            if pick < 0 or self.ranks[at] < self.ranks[pick]:
                pick = at
        return self.recs[0] if pick < 0 else self.recs[pick]

    def drop(self, rec):
        at = self.recs.index(rec)
        self.recs.pop(at)
        self.ranks.pop(at)
