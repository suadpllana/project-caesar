class Lines:
    """A cache as a list of [line, words] records, oldest fill first."""

    def __init__(self, cap):
        self.cap = cap
        self.recs = []

    def find(self, ln):
        for i, rec in enumerate(self.recs):
            if rec[0] == ln:
                return i
        return -1

    def words(self, ln):
        i = self.find(ln)
        return self.recs[i][1] if i >= 0 else None

    def fill(self, ln, words):
        if len(self.recs) == self.cap:
            self.recs.pop(0)
        self.recs.append([ln, words])

    def remove(self, ln):
        i = self.find(ln)
        if i < 0:
            return False
        del self.recs[i]
        return True

    def clear(self):
        had = bool(self.recs)
        self.recs = []
        return had

    def state(self):
        return tuple((ln, tuple(w)) for ln, w in self.recs)
