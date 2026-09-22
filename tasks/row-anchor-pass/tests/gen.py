"""Event files generated from a seed drawn after the agent's container is gone.

The families are shaped around the decisions rather than sampled from the input space. An
unshaped document never pushes a header off, never needs a second pass and never deletes the
item a frame was holding, so most wrong readings score exactly what the right one does on it.
Each family below concentrates one mechanism; the last two exist for the execution limit
rather than for a rule.

  plain   ordinary documents, ordinary scrolling, estimates near the truth
  push    tall headers over short groups, so the next header is inside the band constantly
  pass    estimates far from the real heights, so a pass's own measuring moves the window
  foot    documents barely taller than the viewport, driven to the foot and then edited
  edit    inserts and deletes all over, including deletes that take the held item
  tail    deletes that run to the end of the last group, where nothing survives after the hold
  edge    every height equal and the viewport a multiple of it, so offsets land on boundaries
  cap     a pass cap of one or two under estimates that would need more
  small   one or two groups, a viewport taller than the document, empty groups
  wide    six hundred groups of a hundred rows, driven by two and a half thousand scrolls
  deep    nine hundred groups jumped across end to end, with edits along the way
"""
import random

FAMILIES = (
    ("plain", False),
    ("push", False),
    ("pass", False),
    ("foot", False),
    ("edit", False),
    ("tail", False),
    ("edge", False),
    ("cap", False),
    ("small", False),
    ("wide", True),
    ("deep", True),
)

BIG = 3


class Build:
    """Accumulates a program and keeps the row counts honest for ins and del."""

    def __init__(self, vh, over, pcap):
        self.lines = ["cfg %d %d %d" % (vh, over, pcap)]
        self.n = {}
        self.gids = []

    def group(self, gid, hh, est, lo, hi, rows):
        self.lines.append("g %d %d %d %d %d %d" % (gid, hh, est, lo, hi, rows))
        self.n[gid] = rows
        self.gids.append(gid)

    def scroll(self, d):
        self.lines.append("scroll %d" % d)

    def go(self, p):
        self.lines.append("go %d" % p)

    def size(self, v):
        self.lines.append("size %d" % v)

    def ins(self, gid, pos, k):
        pos = min(pos, self.n[gid])
        self.lines.append("ins %d %d %d" % (gid, pos, k))
        self.n[gid] += k

    def dele(self, gid, pos, k):
        if self.n[gid] == 0:
            return False
        k = min(k, self.n[gid])
        pos = min(pos, self.n[gid] - k)
        self.lines.append("del %d %d %d" % (gid, pos, k))
        self.n[gid] -= k
        return True

    def tail_del(self, gid, k):
        """Delete the last k rows of a group - the only way nothing survives after a hold."""
        if self.n[gid] == 0:
            return False
        k = min(k, self.n[gid])
        self.lines.append("del %d %d %d" % (gid, self.n[gid] - k, k))
        self.n[gid] -= k
        return True


def _stir(b, rng, count, reach, edits=0.0):
    """A run of ordinary events over a document of roughly `reach` pixels."""
    for _ in range(count):
        pick = rng.random()
        if pick < 0.62:
            b.scroll(rng.randint(-reach // 8 - 1, reach // 6 + 1))
        elif pick < 0.76:
            b.go(rng.randint(0, reach))
        elif pick < 0.82:
            b.size(rng.choice([20, 35, 60, 90, 140]))
        elif pick < 0.82 + edits / 2:
            gid = rng.choice(b.gids)
            b.ins(gid, rng.randint(0, 40), rng.randint(1, 3))
        elif pick < 0.82 + edits:
            gid = rng.choice(b.gids)
            b.dele(gid, rng.randint(0, 40), rng.randint(1, 3))
        else:
            b.scroll(rng.choice([-1, 1, -2, 2]))


def plain(rng):
    b = Build(rng.choice([50, 70, 110]), rng.choice([0, 1, 2]), rng.choice([3, 4, 5]))
    ng = rng.randint(3, 7)
    reach = 0
    for k in range(ng):
        hh = rng.randint(8, 18)
        lo = rng.randint(8, 16)
        hi = lo + rng.randint(0, 12)
        est = rng.randint(lo, hi)
        rows = rng.randint(3, 12)
        b.group(k + 1, hh, est, lo, hi, rows)
        reach += hh + rows * est
    _stir(b, rng, rng.randint(18, 30), reach)
    return b.lines


def push(rng):
    b = Build(rng.choice([40, 60, 90]), rng.choice([0, 1]), rng.choice([3, 4]))
    ng = rng.randint(4, 9)
    reach = 0
    for k in range(ng):
        hh = rng.randint(18, 34)
        lo = rng.randint(4, 9)
        hi = lo + rng.randint(0, 5)
        est = rng.randint(lo, hi)
        rows = rng.randint(1, 4)
        b.group(k + 1, hh, est, lo, hi, rows)
        reach += hh + rows * est
    _stir(b, rng, rng.randint(20, 32), reach)
    return b.lines


def hard_pass(rng):
    b = Build(rng.choice([60, 100, 160]), rng.choice([1, 2, 3]), rng.choice([4, 5, 6]))
    ng = rng.randint(3, 6)
    reach = 0
    for k in range(ng):
        hh = rng.randint(6, 16)
        if rng.random() < 0.5:
            est = rng.randint(30, 60)
            lo = rng.randint(3, 6)
            hi = lo + rng.randint(0, 4)
        else:
            est = rng.randint(3, 6)
            lo = rng.randint(30, 50)
            hi = lo + rng.randint(0, 20)
        rows = rng.randint(6, 18)
        b.group(k + 1, hh, est, lo, hi, rows)
        reach += hh + rows * est
    _stir(b, rng, rng.randint(20, 34), max(reach, 40))
    return b.lines


def foot(rng):
    vh = rng.choice([60, 100])
    b = Build(vh, rng.choice([0, 1, 2]), rng.choice([3, 4, 5]))
    ng = rng.randint(2, 5)
    reach = 0
    for k in range(ng):
        hh = rng.randint(6, 14)
        est = rng.randint(6, 30)
        lo = rng.randint(4, 12)
        hi = lo + rng.randint(0, 25)
        rows = rng.randint(2, 7)
        b.group(k + 1, hh, est, lo, hi, rows)
        reach += hh + rows * est
    for _ in range(rng.randint(14, 24)):
        pick = rng.random()
        if pick < 0.30:
            b.go(rng.randint(reach, reach * 2 + 50))
        elif pick < 0.45:
            b.scroll(rng.choice([-1, -2, 1, 2]))
        elif pick < 0.60:
            b.ins(rng.choice(b.gids), rng.randint(0, 6), rng.randint(1, 4))
        elif pick < 0.72:
            b.dele(rng.choice(b.gids), rng.randint(0, 5), rng.randint(1, 3))
        elif pick < 0.84:
            b.size(rng.choice([30, 60, 100, 200]))
        else:
            b.scroll(rng.randint(-40, 60))
    return b.lines


def edit(rng):
    b = Build(rng.choice([50, 80, 120]), rng.choice([0, 1, 2]), rng.choice([3, 4]))
    ng = rng.randint(3, 6)
    reach = 0
    for k in range(ng):
        hh = rng.randint(6, 16)
        est = rng.randint(6, 24)
        lo = rng.randint(5, 14)
        hi = lo + rng.randint(0, 18)
        rows = rng.randint(4, 14)
        b.group(k + 1, hh, est, lo, hi, rows)
        reach += hh + rows * est
    for _ in range(rng.randint(20, 34)):
        pick = rng.random()
        if pick < 0.24:
            b.scroll(rng.randint(-reach // 6 - 1, reach // 5 + 1))
        elif pick < 0.34:
            b.go(rng.randint(0, reach))
        elif pick < 0.64:
            b.ins(rng.choice(b.gids), rng.randint(0, 12), rng.randint(1, 4))
        else:
            b.dele(rng.choice(b.gids), rng.randint(0, 10), rng.randint(1, 4))
    return b.lines


def tail(rng):
    b = Build(rng.choice([45, 70]), rng.choice([0, 1]), rng.choice([3, 4]))
    ng = rng.randint(2, 4)
    reach = 0
    for k in range(ng):
        hh = rng.randint(6, 14)
        est = rng.randint(8, 22)
        lo = rng.randint(5, 12)
        hi = lo + rng.randint(0, 14)
        rows = rng.randint(4, 10)
        b.group(k + 1, hh, est, lo, hi, rows)
        reach += hh + rows * est
    last = b.gids[-1]
    for _ in range(rng.randint(16, 26)):
        pick = rng.random()
        if pick < 0.30:
            b.go(rng.randint(reach // 2, reach + 40))
        elif pick < 0.44:
            b.scroll(rng.randint(-30, 40))
        elif pick < 0.74:
            b.tail_del(last, rng.randint(1, 3))
        elif pick < 0.88:
            b.ins(last, b.n[last], rng.randint(1, 4))
        else:
            b.tail_del(rng.choice(b.gids), rng.randint(1, 2))
    return b.lines


def edge(rng):
    unit = rng.choice([8, 10, 12])
    vh = unit * rng.choice([4, 6, 8])
    b = Build(vh, rng.choice([0, 1, 2]), rng.choice([3, 4]))
    ng = rng.randint(3, 7)
    for k in range(ng):
        rows = rng.randint(2, 8)
        b.group(k + 1, unit, unit, unit, unit, rows)
    span = sum(unit * (1 + b.n[g]) for g in b.gids)
    for _ in range(rng.randint(18, 30)):
        pick = rng.random()
        if pick < 0.55:
            b.go(unit * rng.randint(0, span // unit))
        elif pick < 0.75:
            b.scroll(unit * rng.randint(-4, 5))
        elif pick < 0.85:
            b.scroll(rng.choice([-1, 1]))
        else:
            b.size(unit * rng.choice([2, 3, 5, 9]))
    return b.lines


def cap(rng):
    b = Build(rng.choice([80, 140]), rng.choice([1, 2, 3]), rng.choice([1, 2]))
    ng = rng.randint(3, 6)
    reach = 0
    for k in range(ng):
        hh = rng.randint(8, 20)
        est = rng.choice([2, 3, 70, 90])
        lo = rng.randint(20, 40)
        hi = lo + rng.randint(0, 30)
        rows = rng.randint(6, 16)
        b.group(k + 1, hh, est, lo, hi, rows)
        reach += hh + rows * est
    _stir(b, rng, rng.randint(20, 32), max(reach, 60), edits=0.10)
    return b.lines


def small(rng):
    b = Build(rng.choice([200, 400, 30]), rng.choice([0, 1, 4]), rng.choice([2, 3, 4]))
    ng = rng.randint(1, 2)
    for k in range(ng):
        hh = rng.randint(5, 20)
        est = rng.randint(5, 25)
        lo = rng.randint(4, 20)
        hi = lo + rng.randint(0, 10)
        b.group(k + 1, hh, est, lo, hi, rng.randint(0, 3))
    for _ in range(rng.randint(10, 18)):
        pick = rng.random()
        if pick < 0.34:
            b.go(rng.randint(0, 300))
        elif pick < 0.55:
            b.scroll(rng.randint(-50, 80))
        elif pick < 0.72:
            b.ins(rng.choice(b.gids), rng.randint(0, 3), rng.randint(1, 3))
        elif pick < 0.86:
            b.dele(rng.choice(b.gids), 0, rng.randint(1, 3))
        else:
            b.size(rng.choice([10, 60, 300]))
    return b.lines


def wide(rng):
    b = Build(rng.choice([700, 900]), rng.choice([2, 3]), 4)
    for k in range(600):
        hh = 12 + (k % 7)
        est = 14 + (k % 5)
        lo = 9 + (k % 4)
        hi = lo + 11 + (k % 6)
        b.group(k + 1, hh, est, lo, hi, 100)
    reach = 600 * (14 + 100 * 16)
    where = 0
    for i in range(2500):
        pick = rng.random()
        if pick < 0.80:
            step = rng.randint(-400, 900)
            where = max(0, min(reach, where + step))
            b.scroll(step)
        elif pick < 0.96:
            where = rng.randint(0, reach)
            b.go(where)
        else:
            b.size(rng.choice([500, 700, 1100]))
    return b.lines


def deep(rng):
    b = Build(rng.choice([400, 600]), rng.choice([1, 2]), 4)
    for k in range(900):
        hh = 20 + (k % 11)
        est = 5 + (k % 3)
        lo = 25 + (k % 9)
        hi = lo + 14 + (k % 5)
        b.group(k + 1, hh, est, lo, hi, 30)
    reach = 900 * (25 + 30 * 40)
    for i in range(2500):
        pick = rng.random()
        if pick < 0.55:
            b.go(rng.randint(0, reach))
        elif pick < 0.82:
            b.scroll(rng.randint(-3000, 5000))
        elif pick < 0.92:
            b.ins(rng.randint(1, 900), rng.randint(0, 20), rng.randint(1, 3))
        else:
            b.dele(rng.randint(1, 900), rng.randint(0, 10), rng.randint(1, 2))
    return b.lines


MAKERS = {
    "plain": plain,
    "push": push,
    "pass": hard_pass,
    "foot": foot,
    "edit": edit,
    "tail": tail,
    "edge": edge,
    "cap": cap,
    "small": small,
    "wide": wide,
    "deep": deep,
}


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        for i in range(count):
            rng = random.Random("%s|%s|%d" % (seed, fam, i))
            out.append((fam, "%s-%d" % (fam, i), MAKERS[fam](rng)))
    return out
