from pipe import cut


class Rec:
    __slots__ = ("rid", "n", "w", "first", "parts", "scored", "bands", "bits")

    def __init__(self, rid, n, w):
        self.rid = rid
        self.n = n
        self.w = w
        self.first = 0
        self.parts = 0
        self.scored = 0
        self.bands = []
        self.bits = []


def run(rack, rid, n, w):
    if n < 2:
        rack.sink.skip(rid)
        return None
    rec = Rec(rid, n, w)
    rem = n
    while rem > 0:
        if not rack.up:
            rack.open_win()
        take = cut.fit(rack.room(), rem)
        if take is None:
            rack.shut_win()
            continue
        if rec.parts == 0:
            rec.first = rack.wno
        rec.parts += 1
        rack.put(rid, take)
        rem -= take
        band = rack.bands.cur
        if not rec.bands or rec.bands[-1] != band.idx:
            rec.bands.append(band.idx)
            rec.bits.append([band.idx, 0])
            band.waits += 1
        rec.bits[-1][1] += take - 1
        if rem == 0:
            rec.scored = rec.n - rec.parts
            rack.held.laid_rec(rec)
        if rack.room() == 0 or rem > 0:
            rack.shut_win()
    return rec
