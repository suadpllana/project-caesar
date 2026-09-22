"""The generated half of the graded set.

The seed arrives after the agent's container is gone, so none of these programs existed while
the submission was being written. Each family is shaped at one decision rather than sampled
uniformly: a population of random writes and reads answers almost every read at the present
version and would leave most of the contract untested.

    plain    ordinary traffic, small allowances, the everyday case
    stale    a commit lands inside a covered range and the next read tolerates one version
    torn     two halves of a range whose cached stretches were never correct together
    back     ranges left alone for a long time, so a fetch is correct well before it happened
    deepv    the newest covered version sits several commits back
    short    a horizon small enough to take the older versions away again
    exact    allowances of zero mixed into covered ranges
    holes    ranges with several uncovered stretches between covered ones
    touchy   writes that change nothing, deletes of absent keys, commits that stage nothing
    wide     the scale family over a large key space
    deep     the scale family over a long history
"""

import random

SMALL = ("plain", "stale", "torn", "back", "deepv", "short", "exact", "holes", "touchy")


class Draft(object):
    def __init__(self, horizon, slack=0, cap=8):
        self.lines = ["h %d %d %d" % (horizon, slack, cap)]
        self.staged = 0

    def put(self, k, v):
        self.lines.append("w %d %d" % (k, v))
        self.staged += 1

    def cut(self, k):
        self.lines.append("x %d" % k)
        self.staged += 1

    def seal(self):
        self.lines.append("c")
        self.staged = 0

    def look(self, lo, hi, s):
        self.lines.append("r %d %d %d" % (lo, hi, s))


def _seed_rows(d, rng, span, density):
    for k in range(span):
        if rng.random() < density:
            d.put(k, rng.randrange(1, 90))
    d.seal()


def _span_pick(rng, span, width):
    lo = rng.randrange(0, span - width + 1)
    return lo, lo + width - 1


def plain(rng):
    span = 24
    d = Draft(rng.choice([40, 60, 200]), rng.randrange(0, 4), rng.choice([1, 2, 3, 8]))
    _seed_rows(d, rng, span, 0.5)
    for _ in range(rng.randrange(14, 22)):
        pick = rng.random()
        if pick < 0.45:
            lo, hi = _span_pick(rng, span, rng.randrange(3, 9))
            d.look(lo, hi, rng.randrange(0, 4))
        elif pick < 0.85:
            for _ in range(rng.randrange(1, 3)):
                k = rng.randrange(span)
                if rng.random() < 0.25:
                    d.cut(k)
                else:
                    d.put(k, rng.randrange(1, 90))
            d.seal()
        else:
            lo, hi = _span_pick(rng, span, rng.randrange(6, 14))
            d.look(lo, hi, rng.randrange(0, 6))
    return d.lines


def stale(rng):
    span = 20
    d = Draft(200, rng.randrange(0, 3), rng.choice([2, 3, 8]))
    _seed_rows(d, rng, span, 0.6)
    for _ in range(rng.randrange(5, 8)):
        lo, hi = _span_pick(rng, span, rng.randrange(5, 11))
        d.look(lo, hi, 0)
        d.put(rng.randrange(lo, hi + 1), rng.randrange(1, 90))
        d.seal()
        d.look(lo, hi, rng.randrange(1, 3))
        d.look(lo, hi, 0)
        d.look(lo, hi, rng.randrange(1, 4))
    return d.lines


def torn(rng):
    span = 24
    d = Draft(200, rng.randrange(0, 5), rng.choice([1, 2, 8]))
    _seed_rows(d, rng, span, 0.55)
    for _ in range(rng.randrange(4, 7)):
        cut = rng.randrange(6, span - 6)
        d.look(0, cut - 1, 0)
        d.put(rng.randrange(0, cut), rng.randrange(1, 90))
        d.seal()
        for _ in range(rng.randrange(1, 3)):
            d.put(rng.randrange(cut, span), rng.randrange(1, 90))
            d.seal()
        d.look(cut, span - 1, 0)
        d.look(0, span - 1, rng.randrange(4, 12))
        d.look(0, span - 1, rng.randrange(4, 12))
    return d.lines


def back(rng):
    span = 28
    quiet = rng.randrange(0, 10)
    d = Draft(400, rng.randrange(0, 4), rng.choice([1, 2, 8]))
    _seed_rows(d, rng, span, 0.5)
    for _ in range(rng.randrange(5, 9)):
        d.put(rng.randrange(18, span), rng.randrange(1, 90))
        d.seal()
    for _ in range(rng.randrange(3, 6)):
        d.look(quiet, quiet + rng.randrange(3, 7), rng.randrange(0, 3))
        d.look(quiet, quiet + rng.randrange(3, 7), rng.randrange(8, 30))
        d.put(rng.randrange(18, span), rng.randrange(1, 90))
        d.seal()
        d.look(quiet, span - 1, rng.randrange(8, 30))
    return d.lines


def deepv(rng):
    span = 18
    d = Draft(300, rng.randrange(0, 3), rng.choice([2, 8]))
    _seed_rows(d, rng, span, 0.65)
    for _ in range(rng.randrange(3, 6)):
        d.look(0, span - 1, 0)
        for _ in range(rng.randrange(3, 7)):
            d.put(rng.randrange(span), rng.randrange(1, 90))
            d.seal()
            d.look(0, span - 1, rng.randrange(1, 9))
        d.look(0, span - 1, rng.randrange(6, 14))
    return d.lines


def short(rng):
    span = 20
    d = Draft(rng.randrange(1, 5), rng.randrange(0, 3), rng.choice([2, 8]))
    _seed_rows(d, rng, span, 0.6)
    for _ in range(rng.randrange(6, 10)):
        lo, hi = _span_pick(rng, span, rng.randrange(4, 10))
        d.look(lo, hi, 0)
        for _ in range(rng.randrange(1, 4)):
            d.put(rng.randrange(span), rng.randrange(1, 90))
            d.seal()
        d.look(lo, hi, rng.randrange(1, 7))
    return d.lines


def exact(rng):
    span = 18
    d = Draft(200, rng.randrange(0, 4), rng.choice([1, 2, 3]))
    _seed_rows(d, rng, span, 0.6)
    for _ in range(rng.randrange(8, 13)):
        lo, hi = _span_pick(rng, span, rng.randrange(3, 8))
        d.look(lo, hi, 0)
        d.look(lo, hi, 0)
        if rng.random() < 0.6:
            d.put(rng.randrange(span), rng.randrange(1, 90))
            d.seal()
            d.look(lo, hi, 0)
            d.look(lo, hi, 1)
    return d.lines


def holes(rng):
    span = 30
    d = Draft(200, rng.randrange(0, 6), rng.choice([1, 2, 3, 8]))
    _seed_rows(d, rng, span, 0.5)
    for _ in range(rng.randrange(4, 7)):
        for lo in (2, 10, 20):
            d.look(lo, lo + 2, 0)
        d.look(0, span - 1, rng.randrange(0, 3))
        d.put(rng.randrange(span), rng.randrange(1, 90))
        d.seal()
        d.look(0, span - 1, rng.randrange(0, 5))
    return d.lines


def touchy(rng):
    span = 16
    d = Draft(200, rng.randrange(0, 3), rng.choice([2, 8]))
    held = {}
    for k in range(span):
        if rng.random() < 0.5:
            held[k] = rng.randrange(1, 90)
            d.put(k, held[k])
    d.seal()
    for _ in range(rng.randrange(8, 13)):
        lo, hi = _span_pick(rng, span, rng.randrange(4, 9))
        d.look(lo, hi, rng.randrange(0, 3))
        pick = rng.random()
        if pick < 0.3:
            k = rng.choice(sorted(held)) if held else 0
            d.put(k, held.get(k, 1))
        elif pick < 0.6:
            gone = [k for k in range(span) if k not in held]
            d.cut(rng.choice(gone) if gone else 0)
        elif pick < 0.8:
            k = rng.randrange(span)
            d.put(k, rng.randrange(1, 90))
            d.put(k, rng.randrange(1, 90))
            held[k] = 1
        d.seal()
        d.look(lo, hi, rng.randrange(0, 4))
    return d.lines


ZONE = 128


def wide(rng, steps, rounds):
    span = 2048
    zones = span // ZONE
    d = Draft(1000000, rng.randrange(0, 4), rng.choice([2, 3]))
    for k in range(0, span, 2):
        d.put(k, rng.randrange(1, 90))
    d.seal()
    per = max(1, steps // rounds)
    done = 0
    while done < steps:
        for _ in range(per):
            for _ in range(rng.randrange(1, 4)):
                base = rng.randrange(zones) * ZONE
                d.put(base + rng.randrange(ZONE), rng.randrange(1, 90))
            d.seal()
            done += 1
        base = rng.randrange(zones) * ZONE
        for _ in range(3):
            width = rng.randrange(6, 17)
            lo = base + rng.randrange(ZONE - width + 1)
            d.look(lo, lo + width - 1, rng.randrange(0, 3200))
        lo = base + rng.randrange(ZONE - 48 + 1)
        d.look(lo, lo + 47, rng.randrange(0, 3200))
    return d.lines


def deep(rng, span, steps, rounds):
    d = Draft(1000000, rng.randrange(0, 3), rng.choice([2, 8]))
    for k in range(span):
        if rng.random() < 0.6:
            d.put(k, rng.randrange(1, 90))
    d.seal()
    per = max(1, steps // rounds)
    done = 0
    while done < steps:
        for _ in range(per):
            d.put(rng.randrange(span), rng.randrange(1, 90))
            d.seal()
            done += 1
        for _ in range(3):
            width = rng.randrange(4, 11)
            lo = rng.randrange(span - width + 1)
            d.look(lo, lo + width - 1, rng.randrange(0, 5))
        lo = rng.randrange(span - 48 + 1)
        d.look(lo, lo + 47, done + 4)
    return d.lines


BUILD = {
    "plain": plain,
    "stale": stale,
    "torn": torn,
    "back": back,
    "deepv": deepv,
    "short": short,
    "exact": exact,
    "holes": holes,
    "touchy": touchy,
}

WIDE = ((12000, 300), (8000, 200))
DEEP = ((64, 12000, 1200), (80, 7000, 700))


def programs(seed, per):
    out = []
    for fam in SMALL:
        make = BUILD[fam]
        for i in range(per):
            rng = random.Random("%s/%s/%d" % (seed, fam, i))
            out.append((fam, "%s-%03d" % (fam, i), make(rng)))
    for i, (steps, rounds) in enumerate(WIDE):
        rng = random.Random("%s/wide/%d" % (seed, i))
        out.append(("wide", "wide-%03d" % i, wide(rng, steps, rounds)))
    for i, (span, steps, rounds) in enumerate(DEEP):
        rng = random.Random("%s/deep/%d" % (seed, i))
        out.append(("deep", "deep-%03d" % i, deep(rng, span, steps, rounds)))
    return out
