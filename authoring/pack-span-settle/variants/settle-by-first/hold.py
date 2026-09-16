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
            if rec.bands[0] > band.idx:
                break
            self.at += 1
            self.pay(rec)
        self.flush()

    def pay(self, rec):
        bands = self.rack.bands.all
        d = weigh.div(rec, bands)
        if d == 0:
            self.sink.void(rec.rid)
            for idx in rec.bands:
                bands[idx].share.pop(rec.rid, None)
            return
        num, den = weigh.share(rec, d)
        self.sink.lay(rec.rid, rec.first, rec.parts, rec.scored, num, den)
        for idx in rec.bands:
            band = bands[idx]
            k = band.share.pop(rec.rid, 0)
            if band.keep and k:
                weigh.fold(band, num, den, k)

    def flush(self):
        bands = self.rack.bands.all
        while self.seen <= self.rack.bands.no:
            band = bands[self.seen]
            if not band.shut:
                break
            if band.keep:
                if band.share:
                    break
                self.sink.step(band.idx, band.wins, band.pos, band.num, band.den)
            self.seen += 1
