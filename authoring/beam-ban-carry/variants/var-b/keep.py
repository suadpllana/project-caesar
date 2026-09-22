import bisect


class Pool:
    """Members kept in rank order at all times, so the worst is simply the last of them."""

    def __init__(self, cap):
        self.cap = cap
        self.mem = []
        self.made = 0

    def put(self, fin, ln, path):
        self.made += 1
        row = (-fin, ln, self.made, path)
        bisect.insort(self.mem, row, key=lambda one: one[:3])
        out = []
        while len(self.mem) > self.cap:
            out.append(self.mem.pop())
        return out

    def full(self):
        return len(self.mem) >= self.cap

    def worst(self):
        if not self.mem:
            return None
        return -self.mem[-1][0]

    def held(self):
        return [one[3].held for one in self.mem]

    def listing(self):
        return [(-one[0], one[1], one[3]) for one in self.mem]
