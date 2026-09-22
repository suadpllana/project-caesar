import bisect


class Marks:
    def __init__(self):
        self.hi = []
        self.mk = []

    def note(self, lo, hi, mark):
        self.hi.append(hi)
        self.mk.append(mark)

    def at(self, k):
        return self.mk[bisect.bisect_left(self.hi, k)]
