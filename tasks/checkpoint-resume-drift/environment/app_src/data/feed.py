class Feed:
    def __init__(self):
        self.cur = 0
        self.hd = None

    def draw(self, samp):
        sid = samp.pick(self.cur)
        self.cur += 1
        return sid

    def take(self):
        h = self.hd
        self.hd = None
        return h

    def hold(self, sid, bd):
        self.hd = (sid, bd)

    def snap(self):
        return []

    def rest(self, vec):
        return None
