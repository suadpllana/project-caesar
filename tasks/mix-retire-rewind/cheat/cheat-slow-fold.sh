#!/bin/bash
# right in every rule, and walks where the limit does not allow it
set -euo pipefail

cat > /app/feed/mix.py <<'PYEOF'
from feed import deck


def run(box, slot):
    """Step the mix forward one slot at a time to see where each stretch begins."""
    pat = list(box.pat)
    base = 0
    took = [0] * len(box.lens)
    at = 0
    while at < slot:
        j = pat[(at - base) % len(pat)]
        took[j] += 1
        at += 1
        if box.hold[j] and took[j] >= deck.fits(box, j) * box.hold[j]:
            pat = [s for s in pat if s != j]
            base = at
    return base, tuple(pat), took


def count(pat, j, wide):
    per = pat.count(j)
    if not per:
        return 0
    whole, rest = divmod(wide, len(pat))
    return whole * per + sum(1 for i in range(rest) if pat[i] == j)


def hold(box, slot):
    base, pat, took = run(box, slot)
    return base, pat, tuple(t - count(pat, i, slot - base) for i, t in enumerate(took))


def took(box, slot):
    return list(run(box, slot)[2])


def turn(box, slot):
    base, pat, _took = run(box, slot)
    return pat[(slot - base) % len(pat)]
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
    pool = box.note.setdefault("hand", {})
    got = pool.get((j, ep))
    if got is None:
        order = shuf.hand(box.seed, j, ep, len(box.lens[j]))
        good = [i for i, x in enumerate(order) if box.lens[j][x] <= box.cap]
        got = (order, good)
        if len(pool) > 256:
            pool.clear()
        pool[(j, ep)] = got
    return got


def at(box, j, took):
    if not took:
        return 0, 0
    ep, r = divmod(took - 1, fits(box, j))
    cur = hand(box, j, ep)[1][r] + 1
    if cur == len(box.lens[j]):
        return ep + 1, 0
    return ep, cur


def pick(box, j, took):
    ep, r = divmod(took, fits(box, j))
    order, good = hand(box, j, ep)
    return order[good[r]]
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

