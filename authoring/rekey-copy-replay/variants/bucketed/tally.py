class Tally:
    def __init__(self, place):
        self.place = place

    def close(self):
        placed = 0
        total = 0
        for k, (_a, _b, c) in self.place.fld.items():
            if self.place.up[k]:
                placed += 1
                total += c
        return placed, len(self.place.fld) - placed, total
