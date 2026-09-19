#!/bin/bash
# right in every rule, and walks where the limit does not allow it
set -euo pipefail

cat > /app/feed/mix.py <<'PYEOF'
from feed import deck


def line(box):
    got = box.note.get("line")
    if got is None:
        got = {"segs": [(0, tuple(box.pat), tuple([0] * len(box.lens)))], "shut": False}
        box.note["line"] = got
    return got


def count(pat, j, wide):
    per = pat.count(j)
    if not per:
        return 0
    whole, rest = divmod(wide, len(pat))
    return whole * per + sum(1 for i in range(rest) if pat[i] == j)


def grow(box, slot):
    got = line(box)
    segs = got["segs"]
    while not got["shut"] and segs[-1][0] <= slot:
        start, pat, took = segs[-1]
        span = len(pat)
        first = None
        for j in sorted(set(pat)):
            if not box.hold[j]:
                continue
            left = deck.fits(box, j) * box.hold[j] - took[j]
            spots = [i for i, s in enumerate(pat) if s == j]
            whole, rest = divmod(left - 1, len(spots))
            at = whole * span + spots[rest]
            if first is None or at < first[0]:
                first = (at, j)
        if first is None:
            got["shut"] = True
            break
        at, j = first
        after = tuple(took[i] + count(pat, i, at + 1) for i in range(len(box.lens)))
        segs.append((start + at + 1, tuple(s for s in pat if s != j), after))


def hold(box, slot):
    grow(box, slot)
    segs = line(box)["segs"]
    lo, hi = 0, len(segs) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if segs[mid][0] <= slot:
            lo = mid
        else:
            hi = mid - 1
    return segs[lo]


def took(box, slot):
    start, pat, took = hold(box, slot)
    return [took[j] + count(pat, j, slot - start) for j in range(len(box.lens))]


def turn(box, slot):
    start, pat, _took = hold(box, slot)
    return pat[(slot - start) % len(pat)]
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


def at(box, j, took):
    n = len(box.lens[j])
    lens = box.lens[j]
    cur = ep = 0
    order = shuf.hand(box.seed, j, ep, n)
    left = took
    while left > 0:
        x = order[cur]
        cur += 1
        if cur == n:
            cur = 0
            ep += 1
            order = shuf.hand(box.seed, j, ep, n)
        if lens[x] <= box.cap:
            left -= 1
    return ep, cur


def pick(box, j, took):
    n = len(box.lens[j])
    lens = box.lens[j]
    ep, cur = at(box, j, took)
    order = shuf.hand(box.seed, j, ep, n)
    while True:
        x = order[cur]
        cur += 1
        if cur == n:
            cur = 0
            ep += 1
            order = shuf.hand(box.seed, j, ep, n)
        if lens[x] <= box.cap:
            return x
PYEOF

cat > /app/feed/draw.py <<'PYEOF'
from feed import deck, mix


def slots(box, at, wide):
    took = mix.took(box, at)
    start, pat, _t = mix.hold(box, at)
    span = len(pat)
    out = []
    slot = at
    while len(out) < wide:
        j = pat[(slot - start) % span]
        out.append((j, deck.pick(box, j, took[j])))
        took[j] += 1
        slot += 1
        if box.hold[j] and took[j] >= deck.fits(box, j) * box.hold[j]:
            start, pat, _t = mix.hold(box, slot)
            span = len(pat)
    return out
PYEOF

cat > /app/feed/spot.py <<'PYEOF'
from feed import deck, mix


def at(box, slot):
    took = mix.took(box, slot)
    seen = []
    for j in range(len(box.lens)):
        if box.hold[j] and took[j] >= deck.fits(box, j) * box.hold[j]:
            seen.append(None)
        else:
            ep, cur = deck.at(box, j, took[j])
            seen.append((ep, cur, took[j]))
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

