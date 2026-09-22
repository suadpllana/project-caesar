"""The commands that were issued without their result being taken.

Two orders live over the same set and they are not the same order: `first` is the one
issued earliest, `race` is the one whose answer arrived earliest. A command with no
recorded answer never wins a race, however early it was issued; when none of them has an
answer the earliest issued is returned so the run can name it as what it is waiting on.
"""


class Pend(object):
    def __init__(self):
        self.q = []

    def add(self, rec):
        self.q.append(rec)

    def empty(self):
        return not self.q

    def first(self):
        return self.q[0]

    def fastest(self):
        best = None
        for rec in self.q:
            if rec.pos is None:
                continue
            if best is None or rec.pos < best.pos:
                best = rec
        if best is None:
            return self.q[0]
        return best

    def drop(self, rec):
        self.q.remove(rec)
