#!/bin/bash
# right in every rule, and walks where the limit does not allow it
set -euo pipefail

cat > /app/feed/mix.py <<'PYEOF'
from feed import deck


def turn(ride, slot, pass_by):
    return ride.pat[(slot - ride.base) % len(ride.pat)]


def retire(ride, j):
    box = ride.box
    if not box.hold[j] or ride.out[j]:
        return
    if ride.took[j] >= deck.fits(box, j) * box.hold[j]:
        ride.out[j] = True
        ride.pat = [s for s in ride.pat if s != j]
        ride.base = ride.slot
PYEOF

cat > /app/feed/deck.py <<'PYEOF'
from feed import shuf


def fits(box, j):
    pool = box.note.setdefault("fits", {})
    got = pool.get(j)
    if got is None:
        got = sum(1 for v in box.lens[j] if v <= box.cap)
        pool[j] = got
    return got


def hand(box, j, ep):
    key = ("hand", j)
    got = box.note.get(key)
    if got is None or got[0] != ep:
        got = (ep, shuf.hand(box.seed, j, ep, len(box.lens[j])))
        box.note[key] = got
    return got[1]


def one(box, j, cur, ep):
    n = len(box.lens[j])
    x = hand(box, j, ep)[cur]
    cur += 1
    if cur == n:
        cur = 0
        ep += 1
    return x, cur, ep, box.lens[j][x] <= box.cap
PYEOF

cat > /app/feed/draw.py <<'PYEOF'
from feed import deck, mix


class Ride:
    def __init__(self, box):
        k = len(box.lens)
        self.box = box
        self.slot = 0
        self.base = 0
        self.pat = list(box.pat)
        self.cur = [0] * k
        self.ep = [0] * k
        self.took = [0] * k
        self.out = [False] * k

    def one(self):
        box = self.box
        j = mix.turn(self, self.slot, 0)
        while True:
            x, cur, ep, fits = deck.one(box, j, self.cur[j], self.ep[j])
            self.cur[j], self.ep[j] = cur, ep
            if fits:
                break
        self.took[j] += 1
        self.slot += 1
        mix.retire(self, j)
        return j, x


def ride(box, slot):
    got = box.note.get("ride")
    if got is None or got.slot > slot:
        got = Ride(box)
        box.note["ride"] = got
    while got.slot < slot:
        got.one()
    return got


def slots(box, at, wide):
    got = ride(box, at)
    return [got.one() for _ in range(wide)]
PYEOF

cat > /app/feed/spot.py <<'PYEOF'
from feed import draw


def at(box, slot):
    got = draw.ride(box, slot)
    seen = []
    for j in range(len(box.lens)):
        if got.out[j]:
            seen.append(None)
        else:
            seen.append((got.ep[j], got.cur[j], got.took[j]))
    return seen
PYEOF

cat > /app/feed/deal.py <<'PYEOF'
def split(world, micro, accum, got):
    out = [[[] for _ in range(accum)] for _ in range(world)]
    for o, one in enumerate(got):
        seat = o // world
        out[o % world][seat // micro].append(one)
    return out
PYEOF

cat > /app/feed/keep.py <<'PYEOF'
from feed import spot


def save(box, run):
    wide = run["w"] * run["m"] * run["a"]
    return {"base": run["base"], "done": run["done"], "made": run["made"], "wide": wide,
            "at": spot.at(box, run["base"] + run["made"] * wide)}


def load(box, rec, world, micro, accum):
    return {"base": rec["base"] + rec["done"] * rec["wide"], "done": 0, "made": 0,
            "w": world, "m": micro, "a": accum}
PYEOF

