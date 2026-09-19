from feed import deck, mix


class Ride:
    def __init__(self, box):
        k = len(box.lens)
        self.box = box
        self.slot = 0
        self.base = 0
        self.pat = list(box.pat)
        self.cur = [0] * k
        self.ep = [0] * k
        self.took = [0] * k
        self.out = [False] * k

    def one(self):
        box = self.box
        pass_by = 0
        while True:
            j = mix.turn(self, self.slot, pass_by)
            x, cur, ep, fits = deck.one(box, j, self.cur[j], self.ep[j])
            self.cur[j], self.ep[j] = cur, ep
            mix.retire(self, j)
            if fits:
                break
            pass_by += 1
        self.took[j] += 1
        self.slot += 1
        return j, x


def ride(box, slot):
    got = box.note.get("ride")
    if got is None or got.slot > slot:
        got = Ride(box)
        box.note["ride"] = got
    while got.slot < slot:
        got.one()
    return got


def slots(box, at, wide):
    got = ride(box, at)
    return [got.one() for _ in range(wide)]
