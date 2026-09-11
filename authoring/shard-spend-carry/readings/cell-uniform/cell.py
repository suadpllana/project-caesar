class Cell:
    def __init__(self, n):
        self.n = n
        self.live = True
        self.mi = -1
        self.since = 0
        self.warm = False
        self.v = 0
        self.m = 0
        self.g = 0

    def runs(self, f):
        return [(self.n, self.v if f == 0 else self.m)]

    def take(self, k):
        self.g += k
        self.warm = self.g != 0

    def chill(self):
        self.m = 0

    def spend(self, lo, hi, left):
        if self.g == 0:
            return 0, False
        cost = (self.g if self.g > 0 else -self.g) * (hi - lo)
        if cost > left:
            return 0, True
        self.m += self.g
        self.v -= self.m
        self.g = 0
        self.warm = False
        return cost, False

    def keep(self):
        return [(self.n, self.v, self.m)]

    def put(self, runs):
        self.v = runs[0][1]
        self.m = runs[0][2]
