from pipe import weigh


class Hold:
    def __init__(self, rack, sink):
        self.rack = rack
        self.sink = sink
        self.laid = []
        self.at = 0
        self.seen = 1

    def laid_rec(self, rec):
        self.laid.append(rec)

    def shut_band(self, band):
        while self.at < len(self.laid):
            rec = self.laid[self.at]
            if rec.bands[0] > band.idx:
                break
            self.at += 1
            self.pay(rec)
        self.tell(band)

    def pay(self, rec):
        d = weigh.div(rec, self.rack.bands.all)
        if d == 0:
            self.sink.void(rec.rid)
            return
        num, den = weigh.share(rec, d)
        self.sink.lay(rec.rid, rec.first, rec.parts, rec.scored, num, den)
        for idx in rec.bands:
            band = self.rack.bands.all[idx]
            k = band.share.pop(rec.rid, 0)
            if band.keep:
                weigh.fold(band, num, den, k)

    def tell(self, band):
        if not band.keep:
            self.sink.drop(band.idx, band.wins, band.pos)
            return
        self.sink.step(band.idx, band.wins, band.pos, band.num, band.den)
