from pipe import hold, lay, step


class Rack:
    def __init__(self, sink):
        self.sink = sink
        self.w = 0
        self.sp = 0
        self.fl = 0
        self.slots = []
        self.up = False
        self.wno = 0
        self.bands = step.Bands()
        self.held = hold.Hold(self, sink)

    def wid(self, v):
        self.w = v

    def spn(self, v):
        self.sp = v

    def flr(self, v):
        self.fl = v

    def room(self):
        return self.w - len(self.slots)

    def open_win(self):
        self.bands.want(self)
        self.wno += 1
        self.slots = []
        self.up = True

    def put(self, rid, take):
        self.slots.extend([rid] * take)

    def shut_win(self):
        self.up = False
        self.bands.cur.eat(self.slots)
        self.slots = []
        self.bands.took(self)

    def rec(self, rid, n, w):
        lay.run(self, rid, n, w)

    def seal(self):
        if self.up:
            self.shut_win()
        self.bands.shed(self)
