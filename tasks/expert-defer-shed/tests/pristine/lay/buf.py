class Bufs:
    __slots__ = ("c", "hold", "used")

    def __init__(self, ex, c):
        self.c = c
        self.hold = [{} for _ in range(ex)]
        self.used = [0] * ex

    def room(self, e):
        return self.used[e] < self.c

    def fill(self, e, token):
        slot = self.used[e]
        self.used[e] += 1
        self.hold[e][slot] = token
        return slot

    def drop(self, e, slot):
        del self.hold[e][slot]

    def count(self, e):
        return len(self.hold[e])

    def at(self, e):
        return self.hold[e]
