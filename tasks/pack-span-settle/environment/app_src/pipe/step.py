class Band:
    __slots__ = ("idx", "cap", "flr", "wins", "pos", "share", "shut", "keep",
                 "num", "den")

    def __init__(self, idx, cap, flr):
        self.idx = idx
        self.cap = cap
        self.flr = flr
        self.wins = 0
        self.pos = 0
        self.share = {}
        self.shut = False
        self.keep = False
        self.num = 0
        self.den = 1

    def eat(self, slots):
        share = self.share
        prev = None
        for one in slots:
            if prev is not None:
                self.pos += 1
                share[prev] = share.get(prev, 0) + 1
            prev = one


class Bands:
    def __init__(self):
        self.all = {}
        self.cur = None
        self.no = 0

    def want(self, rack):
        if self.cur is None:
            self.no += 1
            self.cur = Band(self.no, rack.sp, rack.fl)
            self.all[self.no] = self.cur
        return self.cur

    def took(self, rack):
        band = self.cur
        band.wins += 1
        if band.wins >= band.cap:
            self.shed(rack)

    def shed(self, rack):
        band = self.cur
        if band is None:
            return
        self.cur = None
        band.shut = True
        band.keep = band.pos > band.flr
        rack.held.shut_band(band)
