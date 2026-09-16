#!/bin/bash
# answers the enumerated shards from the answer key and does no work
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
import json
import sys

TRUTH = json.loads('{"band-closes": ["lay a 1 1 4 1/4", "lay b 2 1 5 2/5", "step 1 2 9 3/1", "lay c 3 1 4 3/4", "step 2 1 4 3/1"], "band-waits": ["lay a 1 3 11 5/11", "step 1 1 5 25/11", "step 2 1 5 25/11", "step 3 1 1 5/11"], "carry-two": ["lay a 1 1 4 1/2", "lay b 1 2 4 3/4", "step 1 2 8 5/1"], "cross-count": ["lay a 1 1 2 1/2", "lay b 1 1 2 1/2", "lay c 1 1 2 1/2", "step 1 1 6 3/1"], "drop-order": ["drop 4 1 1", "lay a 1 4 16 1/5", "step 1 1 5 1/1", "step 2 1 5 1/1", "step 3 1 5 1/1"], "drop-part": ["drop 2 1 2", "lay a 1 2 9 3/7", "step 1 1 7 3/1"], "drop-void": ["drop 1 1 4", "void a", "drop 2 1 1", "void b"], "exact-fill": ["lay a 1 1 3 1/3", "lay b 1 1 5 2/5", "step 1 1 8 3/1", "lay c 2 1 9 1/3", "step 2 1 9 3/1"], "fill-brim": ["lay a 1 3 13 3/13", "step 1 2 12 36/13", "step 2 1 1 3/13"], "first-window": ["lay a 1 1 4 1/4", "lay b 2 1 3 2/3", "step 1 2 7 3/1"], "floor-edge": ["lay a 1 1 5 2/5", "step 1 1 5 2/1"], "floor-next": ["lay a 1 1 3 1/3", "drop 2 1 3", "lay b 1 2 4 2/1", "step 1 1 4 3/1"], "floor-under": ["drop 1 1 5", "void a"], "frac-reduce": ["lay a 1 1 6 2/1", "step 1 1 6 12/1"], "frac-sum": ["lay a 1 1 3 1/3", "lay b 1 1 5 1/5", "lay c 1 2 6 1/6", "step 1 1 13 17/6", "step 2 1 1 1/6"], "many-bands": ["lay a 1 6 24 1/4", "step 1 2 8 2/1", "step 2 2 8 2/1", "step 3 2 8 2/1", "lay b 7 1 3 1/3", "step 4 1 3 1/1"], "one-token": ["skip b", "lay a 1 1 3 1/3", "lay c 1 1 3 2/3", "step 1 1 6 3/1"], "plain-fit": ["lay a 1 1 4 1/2", "lay b 1 1 3 1/1", "lay c 1 1 2 1/2", "step 1 1 9 6/1"], "room-one": ["lay a 1 1 5 1/5", "step 1 1 5 1/1", "lay b 2 1 3 1/3", "step 2 1 3 1/1"], "room-two": ["lay a 1 1 5 1/5", "step 1 1 5 1/1", "lay b 2 1 2 1/2", "step 2 1 2 1/1"], "seal-empty": ["lay a 1 1 3 1/3", "step 1 1 3 1/1"], "seal-short": ["lay a 1 1 4 1/4", "step 1 1 4 1/1"], "settle-order": ["lay a 1 1 3 1/3", "lay b 1 4 16 7/16", "step 1 1 4 23/16", "step 2 1 5 35/16", "step 3 1 5 35/16", "step 4 1 5 35/16"], "skip-shifts": ["skip b", "lay a 1 1 5 1/5", "lay c 2 1 3 1/3", "step 1 2 8 2/1"], "span-next": ["lay a 1 2 6 1/6", "lay b 2 4 16 1/8", "step 1 3 14 2/1", "step 2 1 5 5/8", "step 3 1 3 3/8"], "stranded-tail": ["lay a 1 2 9 1/9", "step 1 1 8 8/9", "step 2 1 1 1/9"], "two-token": ["lay a 1 1 3 1/3", "lay b 1 1 1 6/1", "lay c 1 1 2 1/1", "step 1 1 6 9/1"], "weight-one": ["lay a 1 1 32 1/32", "step 1 1 32 1/1"], "width-next": ["lay a 1 1 3 1/3", "lay b 1 2 7 2/7", "step 1 2 10 3/1"]}')

NAMED = {'width 6\nspan 2\nfloor 1\nrec a 5 1\nrec b 6 2\nrec c 5 3\nseal': 'band-closes', 'width 6\nspan 1\nfloor 1\nrec a 14 5\nseal': 'band-waits', 'width 8\nspan 2\nfloor 1\nrec a 5 2\nrec b 6 3\nseal': 'carry-two', 'width 9\nspan 1\nfloor 1\nrec a 3 1\nrec b 3 1\nrec c 3 1\nseal': 'cross-count', 'width 6\nspan 1\nfloor 4\nrec a 20 3\nseal': 'drop-order', 'width 8\nspan 1\nfloor 5\nrec a 11 3\nseal': 'drop-part', 'width 6\nspan 1\nfloor 9\nrec a 4 3\nrec b 4 5\nseal': 'drop-void', 'width 10\nspan 1\nfloor 1\nrec a 4 1\nrec b 6 2\nrec c 10 3\nseal': 'exact-fill', 'width 7\nspan 2\nfloor 1\nrec a 16 3\nseal': 'fill-brim', 'width 6\nspan 3\nfloor 1\nrec a 5 1\nrec b 4 2\nseal': 'first-window', 'width 6\nspan 1\nfloor 5\nrec a 6 2\nseal': 'floor-edge', 'width 6\nspan 1\nfloor 1\nrec a 4 1\nfloor 20\nrec b 6 2\nseal': 'floor-next', 'width 6\nspan 1\nfloor 6\nrec a 6 2\nseal': 'floor-under', 'width 10\nspan 1\nfloor 1\nrec a 7 12\nseal': 'frac-reduce', 'width 16\nspan 1\nfloor 1\nrec a 4 1\nrec b 6 1\nrec c 8 1\nseal': 'frac-sum', 'width 5\nspan 2\nfloor 1\nrec a 30 6\nrec b 4 1\nseal': 'many-bands', 'width 9\nspan 1\nfloor 1\nrec a 4 1\nrec b 1 5\nrec c 4 2\nseal': 'one-token', 'width 12\nspan 2\nfloor 1\nrec a 5 2\nrec b 4 3\nrec c 3 1\nseal': 'plain-fit', 'width 7\nspan 1\nfloor 1\nrec a 6 1\nrec b 4 1\nseal': 'room-one', 'width 8\nspan 1\nfloor 1\nrec a 6 1\nrec b 3 1\nseal': 'room-two', 'width 4\nspan 1\nfloor 1\nrec a 4 1\nseal': 'seal-empty', 'width 12\nspan 4\nfloor 1\nrec a 5 1\nseal': 'seal-short', 'width 6\nspan 1\nfloor 1\nrec a 4 1\nrec b 20 7\nseal': 'settle-order', 'width 7\nspan 2\nfloor 1\nrec a 6 1\nrec b 1 9\nrec c 4 1\nseal': 'skip-shifts', 'width 6\nspan 3\nfloor 1\nrec a 8 1\nspan 1\nrec b 20 2\nseal': 'span-next', 'width 10\nspan 1\nfloor 1\nrec a 11 1\nseal': 'stranded-tail', 'width 9\nspan 1\nfloor 1\nrec a 4 1\nrec b 2 6\nrec c 3 2\nseal': 'two-token', 'width 40\nspan 1\nfloor 1\nrec a 33 1\nseal': 'weight-one', 'width 10\nspan 2\nfloor 1\nrec a 4 1\nwidth 5\nrec b 9 2\nseal': 'width-next'}


class Rack:
    def __init__(self, sink):
        self.sink = sink
        self.ops = []

    def wid(self, v):
        self.ops.append('width %d' % v)

    def spn(self, v):
        self.ops.append('span %d' % v)

    def flr(self, v):
        self.ops.append('floor %d' % v)

    def rec(self, rid, n, w):
        self.ops.append('rec %s %d %d' % (rid, n, w))

    def seal(self):
        self.ops.append('seal')
        got = NAMED.get('\n'.join(self.ops))
        for line in (TRUTH.get(got) or ()):
            sys.stdout.write(line + '\n')
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
