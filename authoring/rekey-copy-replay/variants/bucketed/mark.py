import bisect


class Marks:
    def __init__(self):
        self.spans = []

    def note(self, lo, hi, mark):
        self.spans.append((hi, mark))

    def at(self, k):
        i = bisect.bisect_left(self.spans, (k,))
        return self.spans[i][1]
