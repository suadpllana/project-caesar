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
        if not band.keep:
            self.sink.drop(band.idx, band.wins, band.pos)
        while self.at < len(self.laid):
            rec = self.laid[self.at]
            if rec.bands[-1] != band.idx:
                break
            self.at += 1
            self.pay(rec)
        self.flush()

    def pay(self, rec):
        bands = self.rack.bands.all
        d = weigh.div(rec, bands)
        if d:
            num, den = weigh.share(rec, d)
            self.sink.lay(rec.rid, rec.first, rec.parts, rec.scored, num, den)
        else:
            self.sink.void(rec.rid)
        for idx, got in rec.bits:
            band = bands[idx]
            band.waits -= 1
            if d and band.keep and got:
                weigh.fold(band, num, den, got)

    def flush(self):
        bands = self.rack.bands.all
        while self.seen <= self.rack.bands.no:
            band = bands[self.seen]
            if not band.shut:
                break
            if band.keep:
                if band.waits:
                    break
                self.sink.step(band.idx, band.wins, band.pos, band.num, band.den)
            self.seen += 1
