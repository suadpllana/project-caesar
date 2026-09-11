"""Programs generated inside the verifier from a seed drawn after the agent's container is gone.

`cases.py` pins each graded rule with a program small enough to read. This is the other half:
programs a submission cannot have seen, in families shaped around the readings a per-rule set
does not separate.

  plain   ordinary runs - declare, feed gradients, step, ask
  edge    world sizes that do not divide the map, and parameters longer than a whole shard, so
          boundaries land inside parameters and one parameter takes several stops in a step
  stop    budgets tight against the gradients, including single slots nobody can afford, so
          ranks stop early and leave backlogs behind them
  churn   freezes, thaws and world sizes between steps, with queries asked before the step that
          lays the map again
  back    saves and loads straddling a move of the map, so a checkpoint's flat order is not the
          one standing when it is restored
  null    gradients that cancel, budgets consumed to the slot, empty shards and ranks past the
          world size
  grow    parameters declared late and parameters thawed carrying everything they accrued while
          they were out of the map
  wide    the scale family: twelve thousand parameters over twenty-four million slots,
          twenty thousand steps on eight ranks
  deep    the scale family again: six thousand longer parameters over the same number of
          slots, twelve thousand steps on twelve ranks, with budgets that stall a rank
          outright for a stretch and a map that keeps moving under it

`wide` and `deep` are the families the execution limit is about. Everything else is small.
"""
import random

FAMILIES = (
    ("plain", False),
    ("edge", False),
    ("stop", False),
    ("churn", False),
    ("back", False),
    ("null", False),
    ("grow", False),
    ("wide", True),
    ("deep", True),
)


class Site:
    """Accumulates one program and remembers enough to keep it well formed."""

    def __init__(self, rnd):
        self.r = rnd
        self.lines = []
        self.names = []
        self.saved = set()

    def add(self, line):
        self.lines.append(line)

    def par(self, n):
        name = "w%d" % len(self.names)
        self.names.append(name)
        self.add("par %s %d" % (name, n))
        return name

    def pick(self):
        return self.r.choice(self.names)

    def close(self, ranks=6):
        for name in self.names:
            self.add("val " + name)
            self.add("mom " + name)
        for k in range(ranks):
            self.add("own %d" % k)
        return self.lines


def _plain(s):
    s.add("bud %d" % s.r.choice([4, 6, 9, 14, 25, 60]))
    s.add("ws %d" % s.r.randint(1, 4))
    for _ in range(s.r.randint(2, 5)):
        s.par(s.r.randint(1, 7))
    for _ in range(s.r.randint(10, 34)):
        c = s.r.random()
        if c < 0.42:
            s.add("grd %s %d" % (s.pick(), s.r.choice([-3, -2, -1, 1, 1, 2, 3, 4])))
        elif c < 0.82:
            s.add("step")
        elif c < 0.88:
            s.add("ws %d" % s.r.randint(1, 4))
        elif c < 0.94:
            s.add("bud %d" % s.r.choice([2, 5, 11, 30]))
        else:
            s.add("own %d" % s.r.randint(0, 4))
    return s.close()


def _edge(s):
    s.add("bud %d" % s.r.choice([7, 12, 20, 40, 90]))
    s.add("ws %d" % s.r.choice([3, 5, 7]))
    for _ in range(s.r.randint(2, 4)):
        s.par(s.r.randint(1, 3))
    s.par(s.r.randint(14, 30))
    for _ in range(s.r.randint(2, 3)):
        s.par(s.r.randint(1, 5))
    for _ in range(s.r.randint(12, 30)):
        c = s.r.random()
        if c < 0.44:
            s.add("grd %s %d" % (s.pick(), s.r.choice([-2, -1, 1, 1, 2, 3])))
        elif c < 0.80:
            s.add("step")
        elif c < 0.90:
            s.add("ws %d" % s.r.choice([2, 3, 5, 7, 9]))
        else:
            s.add("own %d" % s.r.randint(0, 8))
    return s.close(9)


def _stop(s):
    s.add("bud %d" % s.r.choice([1, 2, 3, 5, 8]))
    s.add("ws %d" % s.r.randint(1, 3))
    for _ in range(s.r.randint(3, 5)):
        s.par(s.r.randint(2, 8))
    for _ in range(s.r.randint(14, 34)):
        c = s.r.random()
        if c < 0.30:
            s.add("grd %s %d" % (s.pick(), s.r.choice([1, 1, 2, 3])))
        elif c < 0.40:
            s.add("grd %s %d" % (s.pick(), s.r.choice([-9, 9, 12, -12])))
        elif c < 0.86:
            s.add("step")
        else:
            s.add("bud %d" % s.r.choice([1, 2, 4, 7, 13, 40]))
    return s.close()


def _churn(s):
    s.add("bud %d" % s.r.choice([5, 9, 18, 40]))
    s.add("ws %d" % s.r.randint(1, 4))
    for _ in range(s.r.randint(3, 6)):
        s.par(s.r.randint(1, 6))
    for _ in range(s.r.randint(16, 40)):
        c = s.r.random()
        if c < 0.24:
            s.add("grd %s %d" % (s.pick(), s.r.choice([-2, -1, 1, 2, 3])))
        elif c < 0.52:
            s.add("step")
        elif c < 0.66:
            s.add("frz %s" % s.pick())
        elif c < 0.80:
            s.add("thw %s" % s.pick())
        elif c < 0.88:
            s.add("ws %d" % s.r.randint(1, 5))
        elif c < 0.94:
            s.add("own %d" % s.r.randint(0, 5))
        else:
            s.add("val %s" % s.pick())
    return s.close()


def _back(s):
    s.add("bud %d" % s.r.choice([6, 12, 25, 60]))
    s.add("ws %d" % s.r.randint(1, 4))
    for _ in range(s.r.randint(3, 6)):
        s.par(s.r.randint(1, 6))
    for _ in range(s.r.randint(18, 42)):
        c = s.r.random()
        if c < 0.26:
            s.add("grd %s %d" % (s.pick(), s.r.choice([-2, -1, 1, 2, 3])))
        elif c < 0.50:
            s.add("step")
        elif c < 0.60:
            tag = "c%d" % s.r.randint(0, 2)
            s.saved.add(tag)
            s.add("save %s" % tag)
        elif c < 0.70 and s.saved:
            s.add("load %s" % s.r.choice(sorted(s.saved)))
        elif c < 0.80:
            s.add("frz %s" % s.pick())
        elif c < 0.88:
            s.add("thw %s" % s.pick())
        elif c < 0.94:
            s.add("ws %d" % s.r.randint(1, 4))
        else:
            s.par(s.r.randint(1, 5))
    return s.close()


def _null(s):
    s.add("bud %d" % s.r.choice([0, 3, 6, 12]))
    s.add("ws %d" % s.r.choice([1, 2, 6, 11]))
    for _ in range(s.r.randint(2, 4)):
        s.par(s.r.randint(1, 4))
    for _ in range(s.r.randint(12, 30)):
        c = s.r.random()
        if c < 0.30:
            k = s.r.choice([1, 2, 3])
            name = s.pick()
            s.add("grd %s %d" % (name, k))
            s.add("grd %s %d" % (name, -k))
        elif c < 0.44:
            s.add("grd %s %d" % (s.pick(), s.r.choice([-2, -1, 1, 2])))
        elif c < 0.76:
            s.add("step")
        elif c < 0.86:
            s.add("bud %d" % s.r.choice([0, 1, 2, 3, 4, 6, 8]))
        elif c < 0.93:
            s.add("ws %d" % s.r.choice([1, 3, 9, 14]))
        else:
            s.add("own %d" % s.r.randint(0, 13))
    return s.close(14)


def _grow(s):
    s.add("bud %d" % s.r.choice([4, 8, 15, 30]))
    s.add("ws %d" % s.r.randint(1, 3))
    for _ in range(s.r.randint(1, 3)):
        s.par(s.r.randint(1, 5))
    for _ in range(s.r.randint(16, 36)):
        c = s.r.random()
        if c < 0.22:
            s.add("grd %s %d" % (s.pick(), s.r.choice([-2, -1, 1, 2, 4])))
        elif c < 0.48:
            s.add("step")
        elif c < 0.60:
            name = s.pick()
            s.add("frz %s" % name)
            for _ in range(s.r.randint(1, 3)):
                s.add("grd %s %d" % (name, s.r.choice([1, 2, 3, 5])))
        elif c < 0.72:
            s.add("thw %s" % s.pick())
        elif c < 0.86 and len(s.names) < 9:
            s.par(s.r.randint(1, 6))
        else:
            s.add("ws %d" % s.r.randint(1, 4))
    return s.close()


def _wide(s):
    npar, steps, ws, bud = 12000, 20000, 8, 7000
    s.add("bud %d" % bud)
    s.add("ws %d" % ws)
    for _ in range(npar):
        s.par(s.r.randint(1800, 2200))
    for t in range(steps):
        for _ in range(3):
            s.add("grd %s %d" % (s.pick(), s.r.choice([1, 1, 2, 3, -1, -2, 7])))
        if t % 100 == 99:
            s.add("%s %s" % (s.r.choice(["frz", "thw"]), s.pick()))
        if t % 900 == 899:
            s.add("ws %d" % s.r.choice([4, 8, 8, 16]))
        if t % 2500 == 2499:
            s.add("save c")
        elif t % 2500 == 1249 and t > 2500:
            s.add("load c")
        s.add("step")
        if t % 2000 == 1000:
            s.add("own %d" % s.r.randrange(8))
    every = s.names
    s.names = every[:12]
    out = s.close(8)
    s.names = every
    return out


def _deep(s):
    npar, steps, ws = 6000, 12000, 12
    s.add("bud 5000")
    s.add("ws %d" % ws)
    for _ in range(npar):
        s.par(s.r.randint(3400, 4600))
    for t in range(steps):
        for _ in range(2):
            s.add("grd %s %d" % (s.pick(), s.r.choice([1, 1, 2, 3, -1, -4, 9])))
        if t % 40 == 39:
            s.add("%s %s" % (s.r.choice(["frz", "thw"]), s.pick()))
        if t % 700 == 699:
            s.add("ws %d" % s.r.choice([5, 12, 12, 23]))
        if t % 1500 == 1499:
            s.add("save d")
        elif t % 1500 == 749 and t > 1500:
            s.add("load d")
        if t % 500 == 200:
            s.add("bud 40")
        elif t % 500 == 260:
            s.add("bud 5000")
        s.add("step")
        if t % 1500 == 800:
            s.add("own %d" % s.r.randrange(12))
    every = s.names
    s.names = every[:10]
    out = s.close(12)
    s.names = every
    return out


MAKE = {
    "plain": _plain,
    "edge": _edge,
    "stop": _stop,
    "churn": _churn,
    "back": _back,
    "null": _null,
    "grow": _grow,
    "wide": _wide,
    "deep": _deep,
}


def one(fam, seed):
    return MAKE[fam](Site(random.Random(seed)))


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        how = max(1, per // 15) if big else per
        for i in range(how):
            name = "%s-%d" % (fam, i)
            out.append((fam, name, one(fam, "%s/%s" % (seed, name))))
    return out
