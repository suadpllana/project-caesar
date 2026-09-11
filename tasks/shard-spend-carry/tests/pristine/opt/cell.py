class Cell:
    def __init__(self, n):
        self.n = n
        self.live = True
        self.v = 0
        self.m = 0
        self.g = 0

    def runs(self, f):
        return [(self.n, self.v if f == 0 else self.m)]

    def take(self, k):
        self.g += k

    def chill(self):
        self.m = 0

    def spend(self, left):
        if self.g == 0:
            return 0, False
        cost = abs(self.g) * self.n
        if cost > left:
            return 0, True
        self.m += self.g
        self.v -= self.m
        self.g = 0
        return cost, False

    def keep(self):
        return [(self.n, self.v, self.m)]

    def put(self, v, m):
        self.v = v
        self.m = m
