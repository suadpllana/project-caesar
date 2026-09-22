class Marks:
    def __init__(self):
        self.spans = []

    def note(self, lo, hi, mark):
        self.spans.append((lo, hi, mark))

    def at(self, k):
        for lo, hi, mark in self.spans:
            if lo < k <= hi:
                return mark
        return 0
