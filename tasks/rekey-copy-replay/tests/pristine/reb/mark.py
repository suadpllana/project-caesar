class Marks:
    def __init__(self):
        self.first = None

    def note(self, lo, hi, mark):
        if self.first is None:
            self.first = mark

    def at(self, k):
        if self.first is None:
            return 0
        return self.first
