"""Programs generated inside the verifier from a seed drawn after the agent's container is gone.

The enumerated set in `cases.py` pins each rule with a program small enough to read. This is
the other half of the grading: programs a submission cannot have seen, in families shaped
around the readings a per-rule set does not separate.

  plain     one line, writes over its own cells, caps and asks - release and cap arithmetic
  share     a still, a graft, and asks on both sides of the pair while each of them writes
  diverge   a graft writing over its inherited cells one at a time, with the line above asked
            between each one, so a charge climbs back as the sharing is undone
  chainy    grafts of grafts, three and four deep, asked from the top and the bottom
  liftup    lifts taken with stills on either side of the origin, before and after asks, and
            drops that were refused before the lift and are not after
  reclaim   drops: of a still nothing else holds, of one a head still holds, of one another
            still holds, and of the still a line was grafted from
  capped    caps met exactly, crossed by one, and crossed only because a graft is holding what
            the put would otherwise have let go of
  cross     a put on one line moving another line's charge, and the refusal that follows
  cutback   cuts against stills and grafts, and the blocks a cut does not release
  wide      the scale family: a broad map with thousands of stills taken over it
  deep      the scale family: a broad map under a cap, with every put measured and asked

`wide` and `deep` are the families the execution limit is about. Everything else is small.
"""
import random

FAMILIES = (
    ("plain", False),
    ("share", False),
    ("diverge", False),
    ("chainy", False),
    ("liftup", False),
    ("reclaim", False),
    ("capped", False),
    ("cross", False),
    ("cutback", False),
    ("wide", True),
    ("deep", True),
)

CELLS = 12


class Site:
    """A program under construction, with just enough state to stay well formed."""

    def __init__(self, r):
        self.r = r
        self.out = []
        self.lines = []
        self.stills = []
        self.origins = set()
        self.nline = 0
        self.nstill = 0

    def line(self):
        self.nline += 1
        name = "L%d" % self.nline
        self.lines.append(name)
        self.out.append("line %s" % name)
        return name

    def still(self, name):
        self.nstill += 1
        one = "s%d" % self.nstill
        self.stills.append(one)
        self.out.append("still %s %s" % (name, one))
        return one

    def graft(self, still):
        self.nline += 1
        name = "L%d" % self.nline
        self.lines.append(name)
        self.origins.add(still)
        self.out.append("graft %s %s" % (still, name))
        return name

    def put(self, name, lo, hi, size):
        self.out.append("put %s %d %d %d" % (name, lo, hi, size))

    def cut(self, name, lo, hi):
        self.out.append("cut %s %d %d" % (name, lo, hi))

    def cap(self, name, size):
        self.out.append("cap %s %d" % (name, size))

    def lift(self, name):
        self.out.append("lift %s" % name)

    def drop(self, still):
        self.out.append("drop %s" % still)
        if still in self.stills:
            self.stills.remove(still)

    def ask(self, name):
        self.out.append("ask %s" % name)

    def at(self, name, cell):
        self.out.append("at %s %d" % (name, cell))

    def span(self, wide=3):
        lo = self.r.randrange(CELLS)
        return lo, min(CELLS - 1, lo + self.r.randrange(wide))

    def close(self):
        for name in self.lines:
            self.ask(name)
        return self.out


def plain(s):
    a = s.line()
    s.put(a, 0, 5, s.r.randrange(2, 9))
    for _ in range(s.r.randint(6, 12)):
        pick = s.r.random()
        if pick < 0.45:
            lo, hi = s.span()
            s.put(a, lo, hi, s.r.randrange(1, 9))
        elif pick < 0.6:
            lo, hi = s.span()
            s.cut(a, lo, hi)
        elif pick < 0.75:
            s.still(a)
        elif pick < 0.85:
            s.cap(a, s.r.randrange(10, 80))
        else:
            s.ask(a)
    s.at(a, s.r.randrange(CELLS))
    return s.close()


def share(s):
    a = s.line()
    s.put(a, 0, s.r.randrange(3, 8), s.r.randrange(2, 7))
    one = s.still(a)
    b = s.graft(one)
    for _ in range(s.r.randint(4, 9)):
        who = a if s.r.random() < 0.5 else b
        pick = s.r.random()
        if pick < 0.5:
            lo, hi = s.span(2)
            s.put(who, lo, hi, s.r.randrange(1, 8))
        elif pick < 0.65:
            lo, hi = s.span(2)
            s.cut(who, lo, hi)
        elif pick < 0.8:
            s.still(who)
        else:
            s.ask(who)
    return s.close()


def diverge(s):
    a = s.line()
    top = s.r.randrange(4, 9)
    s.put(a, 0, top, s.r.randrange(2, 7))
    one = s.still(a)
    b = s.graft(one)
    if s.r.random() < 0.5:
        s.cut(a, 0, s.r.randrange(1, top))
    for cell in range(top + 1):
        s.put(b, cell, cell, s.r.randrange(1, 6))
        if s.r.random() < 0.6:
            s.ask(a)
        if s.r.random() < 0.4:
            s.ask(b)
    return s.close()


def chainy(s):
    a = s.line()
    s.put(a, 0, 7, s.r.randrange(2, 6))
    here = a
    for _ in range(s.r.randint(2, 4)):
        one = s.still(here)
        here = s.graft(one)
        lo, hi = s.span(2)
        s.put(here, lo, hi, s.r.randrange(1, 7))
        if s.r.random() < 0.5:
            s.cut(here, s.r.randrange(CELLS), s.r.randrange(CELLS))
        s.ask(a)
        s.ask(here)
    if s.r.random() < 0.5:
        s.lift(here)
        s.ask(a)
        s.ask(here)
    return s.close()


def liftup(s):
    a = s.line()
    s.put(a, 0, 6, s.r.randrange(2, 7))
    before = [s.still(a) for _ in range(s.r.randint(1, 2))]
    s.put(a, 0, 2, s.r.randrange(1, 6))
    mid = s.still(a)
    b = s.graft(mid)
    s.put(a, 3, 5, s.r.randrange(1, 6))
    after = [s.still(a) for _ in range(s.r.randint(1, 2))]
    s.cut(a, 0, s.r.randrange(0, 4))
    if s.r.random() < 0.6:
        s.put(b, 0, s.r.randrange(0, 3), s.r.randrange(1, 6))
    s.drop(before[0])
    s.ask(a)
    s.ask(b)
    s.lift(b)
    s.ask(a)
    s.ask(b)
    for one in before[1:] + after + [mid]:
        s.drop(one)
        s.ask(a)
        s.ask(b)
    if s.r.random() < 0.5:
        s.lift(a)
        s.ask(a)
        s.ask(b)
    return s.close()


def reclaim(s):
    a = s.line()
    s.put(a, 0, 6, s.r.randrange(2, 8))
    one = s.still(a)
    s.put(a, 0, 2, s.r.randrange(1, 7))
    two = s.still(a)
    b = s.graft(two) if s.r.random() < 0.6 else None
    s.cut(a, s.r.randrange(0, 3), s.r.randrange(3, 7))
    three = s.still(a)
    order = [one, two, three]
    s.r.shuffle(order)
    for still in order:
        s.drop(still)
        s.ask(a)
        if b is not None:
            s.ask(b)
    if b is not None:
        s.lift(b)
        for still in [one for one in order if one in s.stills]:
            s.drop(still)
        s.ask(a)
        s.ask(b)
    return s.close()


def capped(s):
    a = s.line()
    size = s.r.randrange(2, 6)
    wide = s.r.randrange(3, 7)
    s.put(a, 0, wide, size)
    s.cap(a, (wide + 1) * size + s.r.randrange(0, 3))
    for _ in range(s.r.randint(5, 10)):
        pick = s.r.random()
        lo, hi = s.span(2)
        if pick < 0.5:
            s.put(a, lo, hi, s.r.randrange(1, 7))
        elif pick < 0.65:
            s.still(a)
        elif pick < 0.8:
            s.cut(a, lo, hi)
        elif pick < 0.9:
            s.cap(a, s.r.randrange(8, 70))
        else:
            s.ask(a)
        s.at(a, lo)
    return s.close()


def cross(s):
    a = s.line()
    size = s.r.randrange(3, 7)
    wide = s.r.randrange(4, 8)
    s.put(a, 0, wide, size)
    one = s.still(a)
    b = s.graft(one)
    s.cap(b, (wide + 1) * size // 2 + s.r.randrange(0, 4))
    s.cap(a, (wide + 1) * size + s.r.randrange(0, 5))
    for cell in range(wide + 1):
        who = a if s.r.random() < 0.5 else b
        s.put(who, cell, cell, s.r.randrange(1, 5))
        s.ask(a)
        s.ask(b)
    s.drop(one) if one in s.stills else None
    s.ask(a)
    s.ask(b)
    return s.close()


def cutback(s):
    a = s.line()
    s.put(a, 0, 7, s.r.randrange(2, 7))
    one = s.still(a)
    s.cut(a, 0, s.r.randrange(1, 5))
    s.ask(a)
    b = s.graft(one)
    s.ask(a)
    s.ask(b)
    s.cut(b, 0, s.r.randrange(1, 5))
    s.ask(a)
    s.ask(b)
    for _ in range(s.r.randint(2, 5)):
        who = a if s.r.random() < 0.5 else b
        lo, hi = s.span(3)
        if s.r.random() < 0.5:
            s.cut(who, lo, hi)
        else:
            s.put(who, lo, hi, s.r.randrange(1, 6))
        s.ask(who)
    s.drop(one) if one in s.stills else None
    return s.close()


def wide(s):
    """A broad map with thousands of stills taken over it."""
    a = s.line()
    cells = 30000
    step = 400
    for lo in range(0, cells, step):
        s.put(a, lo, lo + step - 1, s.r.randrange(2, 9))
    for i in range(6000):
        s.still(a)
        lo = s.r.randrange(cells - 4)
        s.put(a, lo, lo + s.r.randrange(4), s.r.randrange(1, 9))
        if i % 300 == 0:
            s.ask(a)
    one = s.still(a)
    b = s.graft(one)
    s.put(b, 0, 40, 3)
    s.ask(a)
    s.ask(b)
    return s.close()


def deep(s):
    """A broad map under a cap, with every put measured against it and asked after."""
    a = s.line()
    cells = 24000
    step = 300
    for lo in range(0, cells, step):
        s.put(a, lo, lo + step - 1, 4)
    one = s.still(a)
    b = s.graft(one)
    s.cap(a, 4 * cells + 600)
    s.cap(b, 3000)
    for i in range(24000):
        who = a if i % 3 else b
        lo = s.r.randrange(cells - 3)
        s.put(who, lo, lo + s.r.randrange(3), s.r.randrange(1, 7))
        if i % 400 == 0:
            s.ask(a)
            s.ask(b)
    s.ask(a)
    s.ask(b)
    return s.close()


SHAPE = {
    "plain": plain,
    "share": share,
    "diverge": diverge,
    "chainy": chainy,
    "liftup": liftup,
    "reclaim": reclaim,
    "capped": capped,
    "cross": cross,
    "cutback": cutback,
    "wide": wide,
    "deep": deep,
}


def one(fam, seed):
    return SHAPE[fam](Site(random.Random(seed)))


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        how = max(1, per // 15) if big else per
        for i in range(how):
            name = "%s-%d" % (fam, i)
            out.append((fam, name, one(fam, "%s/%s" % (seed, name))))
    return out
