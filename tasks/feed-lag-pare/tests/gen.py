"""Programs generated from a seed drawn after the agent's container is gone.

The families are shaped around the graded decisions rather than sampled from the command
space. An unshaped population almost never puts a pin below a stretch whose entries cancel
out, never leaves a key half collapsed and never separates a feed's covered range from the
rest of the key space, so most of the wrong readings score exactly what the right one does.
Each family below concentrates one mechanism; the last two exist for the execution limit
rather than for a rule.

  plain    ordinary traffic: a few marks, a feed or two that keeps up, moderate budgets
  nofeed   no feed at all, so every key collapses to the marks - the case the retrieved plan
           gets right, and the one an overconservative service fails
  lag      a feed that never acknowledges, so most of the log sits in its kept region
  part     feeds over narrow key ranges beside keys no feed covers
  nil      stretches whose entries cancel out, so the span keeps nothing
  gone     deletes and adds onto absent keys, including spans absent at both ends
  tight    budgets that stop a pare part way, leaving keys half collapsed
  late     a budgeted pare, then an unmark that merges a collapsed span with a stretch that
           cancels out - where the surviving entry has to move
  tie      many pairs removing the same number of entries, for the two tie-breaks
  edge     acknowledgements below the position, at the head and past it; two pins at one
           point; reads at every live pin
  wide     many keys, a large standing log and many pares
  deep     few keys, long chains, and pares that collapse a great deal at once
"""
import random

FAMILIES = (
    ("plain", False),
    ("nofeed", False),
    ("lag", False),
    ("part", False),
    ("nil", False),
    ("gone", False),
    ("tight", False),
    ("late", False),
    ("tie", False),
    ("edge", False),
    ("wide", True),
    ("deep", True),
)

BIG = 3


class Build:
    """Tracks enough state to emit only well-formed programs."""

    def __init__(self, rng, keys):
        self.rng = rng
        self.keys = keys
        self.lines = []
        self.head = 0
        self.marks = []
        self.feeds = {}
        self.used = 0

    def name(self):
        self.used += 1
        return "p%d" % self.used

    def entry(self, key, kind=None, span=9):
        kind = kind or self.rng.choice(["set", "add", "add", "add", "del"])
        if kind == "del":
            self.lines.append("del %d" % key)
        else:
            self.lines.append("%s %d %d" % (kind, key, self.rng.randint(-span, span)))
        self.head += 1

    def step(self, key, by):
        self.lines.append("add %d %d" % (key, by))
        self.head += 1

    def mark(self):
        name = self.name()
        self.lines.append("mark %s" % name)
        self.marks.append(name)
        return name

    def unmark(self, name=None):
        if not self.marks:
            return None
        if name is None:
            name = self.marks[self.rng.randrange(len(self.marks))]
        self.marks.remove(name)
        self.lines.append("unmark %s" % name)
        return name

    def feed(self, lo, hi):
        name = self.name()
        self.lines.append("feed %s %d %d" % (name, lo, hi))
        self.feeds[name] = [self.head, lo, hi]
        return name

    def ack(self, name, seq):
        rec = self.feeds[name]
        self.lines.append("ack %s %d" % (name, seq))
        if seq > rec[0] and seq <= self.head:
            rec[0] = seq

    def close(self, name):
        if name in self.feeds:
            self.lines.append("close %s" % name)
            del self.feeds[name]

    def read(self):
        picks = self.marks + sorted(self.feeds)
        if not picks:
            return
        who = self.rng.choice(picks)
        if who in self.feeds:
            _at, lo, hi = self.feeds[who]
            key = self.rng.randint(lo, hi)
        else:
            key = self.rng.randrange(self.keys)
        self.lines.append("read %s %d" % (who, key))

    def pare(self, budget):
        self.lines.append("pare %d" % max(0, budget))


def _plain(rng):
    keys = rng.randint(4, 8)
    b = Build(rng, keys)
    for _ in range(rng.randint(3, 7)):
        b.entry(rng.randrange(keys))
    b.mark()
    name = b.feed(0, keys - 1)
    for _round in range(rng.randint(3, 6)):
        for _ in range(rng.randint(2, 6)):
            b.entry(rng.randrange(keys))
        if rng.random() < 0.5:
            b.mark()
        if rng.random() < 0.6:
            b.ack(name, rng.randint(1, b.head))
        if rng.random() < 0.4:
            b.read()
        b.pare(rng.randint(2, 10))
    b.read()
    b.pare(rng.randint(0, 4))
    return b.lines


def _nofeed(rng):
    keys = rng.randint(3, 6)
    b = Build(rng, keys)
    for _round in range(rng.randint(3, 6)):
        for _ in range(rng.randint(2, 5)):
            b.entry(rng.randrange(keys))
        if rng.random() < 0.7:
            b.mark()
        if rng.random() < 0.3:
            b.unmark()
        b.read()
        b.pare(rng.randint(0, 8))
    b.pare(0)
    return b.lines


def _lag(rng):
    keys = rng.randint(3, 6)
    b = Build(rng, keys)
    for _ in range(rng.randint(2, 4)):
        b.entry(rng.randrange(keys))
    b.feed(0, keys - 1)
    b.mark()
    for _round in range(rng.randint(3, 6)):
        for _ in range(rng.randint(2, 5)):
            b.entry(rng.randrange(keys))
        if rng.random() < 0.5:
            b.mark()
        b.read()
        b.pare(0)
    b.pare(0)
    return b.lines


def _part(rng):
    keys = rng.randint(6, 9)
    b = Build(rng, keys)
    for _ in range(rng.randint(3, 6)):
        b.entry(rng.randrange(keys))
    cut = rng.randint(1, keys - 3)
    slow = b.feed(0, cut)
    b.mark()
    for _round in range(rng.randint(3, 6)):
        for _ in range(rng.randint(3, 6)):
            b.entry(rng.randrange(keys))
        if rng.random() < 0.4:
            b.feed(cut + 1, keys - 1)
        if rng.random() < 0.3:
            b.ack(slow, rng.randint(1, b.head))
        b.read()
        b.pare(rng.randint(0, 6))
    b.close(slow)
    b.pare(0)
    for name in list(b.feeds):
        b.close(name)
    b.pare(0)
    return b.lines


def _nil(rng):
    keys = rng.randint(2, 4)
    b = Build(rng, keys)
    for _round in range(rng.randint(3, 6)):
        key = rng.randrange(keys)
        by = rng.randint(1, 6)
        b.step(key, by)
        for _ in range(rng.randint(0, 2)):
            b.entry(rng.randrange(keys), "add")
        b.step(key, -by)
        b.mark()
        b.pare(rng.randint(0, 5))
    b.pare(0)
    return b.lines


def _gone(rng):
    keys = rng.randint(2, 4)
    b = Build(rng, keys)
    for _round in range(rng.randint(3, 6)):
        key = rng.randrange(keys)
        b.entry(key, "del")
        b.entry(key, "add")
        b.entry(key, "del")
        if rng.random() < 0.5:
            b.entry(rng.randrange(keys), "set")
        b.mark()
        b.read()
        b.pare(rng.randint(0, 4))
    b.pare(0)
    return b.lines


def _tight(rng):
    keys = rng.randint(4, 6)
    b = Build(rng, keys)
    for _round in range(rng.randint(3, 6)):
        for _ in range(rng.randint(4, 8)):
            b.entry(rng.randrange(keys))
        b.mark()
        b.pare(rng.randint(3, 9))
        if rng.random() < 0.5:
            b.unmark()
        b.pare(rng.randint(1, 6))
    b.pare(0)
    return b.lines


def _late(rng):
    """A budget that stops with a key half collapsed, then a pin goes and the spans merge.

    The stretch above the pin cancels out, so collapsing it keeps nothing and the entries
    that stood there leave the log. When the pin goes, the entry the merged stretch keeps
    has to be the last one the log still holds, which is now below where the program last
    wrote. The budget is worked out here rather than drawn, because the shape only exists
    when the pare stops in exactly the right place.
    """
    keys = rng.randint(2, 4)
    b = Build(rng, keys)
    key = rng.randrange(keys)
    spare = [k for k in range(keys) if k != key]
    pairs = rng.randint(1, 3)
    below = rng.randint(2, 2 * pairs)
    for _ in range(below):
        b.step(key, rng.randint(1, 6))
    noise = 0
    for other in spare:
        if rng.random() < 0.6:
            b.entry(other, "set")
            noise += 1
    pin = b.mark()
    for other in spare:
        if rng.random() < 0.5:
            b.entry(other, "set")
            noise += 1
    for _ in range(pairs):
        by = rng.randint(1, 7)
        b.step(key, by)
        b.step(key, -by)
    b.pare(below + noise)
    if rng.random() < 0.4:
        b.read()
    b.unmark(pin)
    b.pare(0)
    return b.lines


def _tie(rng):
    """Two stretches, every pair in them removing exactly one entry.

    A budget that stops part way through equal pairs is the only thing that shows which
    order they went in, so the number collapsed is chosen strictly between one and all of
    them: the pairs that survive say which span top and which key the tie went to.
    """
    keys = rng.randint(2, 4)
    b = Build(rng, keys)
    for key in range(keys):
        b.entry(key, "set", 3)
        b.step(key, 1)
    b.mark()
    for key in range(keys):
        b.step(key, 1)
        b.step(key, 1)
    b.mark()
    take = rng.randint(1, 2 * keys - 1)
    b.pare(4 * keys - take)
    if rng.random() < 0.5:
        b.read()
    return b.lines


def _edge(rng):
    keys = rng.randint(3, 5)
    b = Build(rng, keys)
    for _ in range(rng.randint(2, 4)):
        b.entry(rng.randrange(keys))
    one = b.feed(0, keys - 1)
    b.mark()
    b.mark()
    for _round in range(rng.randint(3, 5)):
        for _ in range(rng.randint(2, 4)):
            b.entry(rng.randrange(keys))
        pick = rng.random()
        if pick < 0.34:
            b.ack(one, rng.randint(0, b.feeds[one][0]))
        elif pick < 0.67:
            b.ack(one, b.head)
        else:
            b.ack(one, b.head + rng.randint(1, 4))
        b.read()
        b.unmark()
        b.mark()
        b.pare(rng.randint(0, 5))
    b.read()
    b.pare(0)
    return b.lines


def _wide(rng, keys=1200, fill=60000, rounds=1100, burst=8, marks=60, feeds_n=3, cover=0.2):
    b = Build(rng, keys)
    reach = max(feeds_n, int(keys * cover))
    edges = [(i * reach) // feeds_n for i in range(feeds_n + 1)]
    feeds = [b.feed(edges[i], edges[i + 1] - 1) for i in range(feeds_n)]
    gap = fill // (marks + 1)
    for i in range(fill):
        b.entry(rng.randrange(keys), None, 4)
        if i % gap == gap - 1 and len(b.marks) < marks:
            b.mark()
    for step in range(rounds):
        for _ in range(burst):
            b.entry(rng.randrange(keys), None, 4)
        if step % 4 == 0:
            b.ack(feeds[(step // 4) % feeds_n], b.head - rng.randint(0, 40))
        if step % 370 == 369:
            b.unmark()
        b.pare(0)
    b.read()
    b.pare(0)
    return b.lines


def _deep(rng, keys=24, fill=24000, gap=130):
    b = Build(rng, keys)
    for i in range(fill):
        b.entry(rng.randrange(keys), None, 4)
        if i % gap == gap - 1:
            b.mark()
    for cut in (18000, 12000, 6000):
        b.pare(cut)
        b.unmark()
    b.pare(0)
    return b.lines


MAKERS = {
    "plain": _plain,
    "nofeed": _nofeed,
    "lag": _lag,
    "part": _part,
    "nil": _nil,
    "gone": _gone,
    "tight": _tight,
    "late": _late,
    "tie": _tie,
    "edge": _edge,
    "wide": _wide,
    "deep": _deep,
}


def programs(seed, per):
    """Every graded program: `per` from each ordinary family and BIG from each large one."""
    out = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        for i in range(count):
            rng = random.Random("%s|%s|%d" % (seed, fam, i))
            out.append((fam, "%s-%d" % (fam, i), MAKERS[fam](rng)))
    return out
