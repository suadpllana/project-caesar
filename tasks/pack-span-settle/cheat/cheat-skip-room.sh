#!/bin/bash
# a passed over record still takes the slot it would have used
set -euo pipefail

cat > /app/pipe/cut.py <<'PYEOF'
def fit(room, rem):
    most = room if room < rem else rem
    if most < 2:
        return None
    left = rem - most
    if left == 0 or left >= 2:
        return most
    if most > 2:
        return most - 1
    return None
PYEOF

cat > /app/pipe/win.py <<'PYEOF'
from pipe import hold, lay, step


class Rack:
    def __init__(self, sink):
        self.sink = sink
        self.w = 0
        self.sp = 0
        self.fl = 0
        self.ww = 0
        self.fill = 0
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
        return self.ww - self.fill

    def open_win(self):
        self.bands.want(self)
        self.wno += 1
        self.ww = self.w
        self.fill = 0
        self.up = True

    def put(self, rid, take):
        self.fill += take
        self.bands.cur.put(rid, take)

    def shut_win(self):
        self.up = False
        self.fill = 0
        self.bands.took(self)

    def rec(self, rid, n, w):
        lay.run(self, rid, n, w)

    def seal(self):
        if self.up:
            self.shut_win()
        self.bands.shed(self)
PYEOF

cat > /app/pipe/lay.py <<'PYEOF'
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
        if not rack.up:
            rack.open_win()
        rack.put(rid, 1)
        if rack.room() == 0:
            rack.shut_win()
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
        if rem == 0:
            rec.scored = rec.n - rec.parts
            rack.held.laid_rec(rec)
        if rack.room() == 0 or rem > 0:
            rack.shut_win()
    return rec
PYEOF

cat > /app/pipe/step.py <<'PYEOF'
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

    def put(self, rid, take):
        got = take - 1
        if got:
            self.pos += got
        self.share[rid] = self.share.get(rid, 0) + got


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
        band.keep = band.pos >= band.flr
        rack.held.shut_band(band)
PYEOF

cat > /app/pipe/hold.py <<'PYEOF'
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
PYEOF

cat > /app/pipe/weigh.py <<'PYEOF'
from pipe import frac


def div(rec, bands):
    out = 0
    for idx in rec.bands:
        band = bands[idx]
        if band.keep:
            out += band.share.get(rec.rid, 0)
    return out


def share(rec, d):
    return frac.norm(rec.w, d)


def fold(band, num, den, k):
    n = band.num * den + num * k * band.den
    d = band.den * den
    band.num, band.den = frac.norm(n, d)
PYEOF
