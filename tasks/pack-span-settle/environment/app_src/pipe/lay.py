from pipe import cut


class Rec:
    __slots__ = ("rid", "n", "w", "first", "parts", "scored", "bands")

    def __init__(self, rid, n, w):
        self.rid = rid
        self.n = n
        self.w = w
        self.first = 0
        self.parts = 0
        self.scored = 0
        self.bands = []


def run(rack, rid, n, w):
    if n < 2:
        rack.sink.skip(rid)
    rec = Rec(rid, n, w)
    rec.first = rack.wno if rack.up else rack.wno + 1
    rem = n
    while rem > 0:
        if not rack.up:
            rack.open_win()
        take = cut.fit(rack.room(), rem)
        if take is None:
            rack.shut_win()
            continue
        rec.parts += 1
        rack.put(rid, take)
        rem -= take
        band = rack.bands.cur
        if not rec.bands or rec.bands[-1] != band.idx:
            rec.bands.append(band.idx)
        if rem == 0:
            rec.scored = rec.n - 1
            rack.held.laid_rec(rec)
        if rack.room() == 0 or rem > 0:
            rack.shut_win()
    return rec
