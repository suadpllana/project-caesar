class Tally:
    def __init__(self, place):
        self.place = place

    def close(self):
        placed = len(self.place.fld)
        aside = self.place.wait.count()
        total = 0
        for _a, _b, c in self.place.fld.values():
            total += c
        return placed, aside, total
