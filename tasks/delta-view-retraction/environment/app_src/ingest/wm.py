class Wm:
    def __init__(self, lag):
        self.lag = lag
        self.hi = 0
        self.cur = 0

    def observe(self, ts):
        if ts > self.hi:
            self.hi = ts
        nw = self.hi - self.lag
        if nw > self.cur:
            self.cur = nw
        return self.cur
