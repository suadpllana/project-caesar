class Place:
    def __init__(self, launch):
        self.slots = [[None] * launch.slots for _ in range(launch.sms)]
        self.grid = launch.grid
        self.waiting = 0
        self.leaving = []

    def exit(self, b):
        self.leaving.append(b)

    def cycle(self, blocks, t):
        for b in self.leaving:
            self.slots[b.sm][b.slot] = None
        self.leaving = []
        new = []
        while self.waiting < self.grid:
            room = [row.count(None) for row in self.slots]
            most = max(room)
            if most == 0:
                break
            sm = room.index(most)
            k = self.slots[sm].index(None)
            b = blocks[self.waiting]
            self.slots[sm][k] = b
            b.sm, b.slot, b.at = sm, k, t
            self.waiting += 1
            new.append(b)
        return new
