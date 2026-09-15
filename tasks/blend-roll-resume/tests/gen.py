"""Scripts generated from a seed drawn after the agent's container is gone.

Nine families, each shaped at one place the rules meet rather than at random, because an
unshaped population does not exercise a mechanism it never builds:

  plain  ordinary running, no caps, nothing restarted - the side an overconservative feed fails
  roll   sources small enough that epochs turn over inside a single step
  part   caps timed to fall part way through a step, so the rebase happens mid-step
  swap   weights changed while the run is going
  same   save, stop and run again with the same blend and the same width
  width  save, stop and run again at a different rank count, micro-batch and accumulation
  late   a departure or a reweighing between the checkpoint and the stop
  join   a source declared mid-run, some of them after the checkpoint was written
  big    the scale family: millions of steps with departures spread along them

`programs(seed, per)` is a pure function of its arguments, so the grader and the worker build
the same scripts without sharing anything but the seed.
"""
import hashlib
import random

FAMILIES = (
    ("plain", False),
    ("roll", False),
    ("part", False),
    ("swap", False),
    ("same", False),
    ("width", False),
    ("late", False),
    ("join", False),
    ("big", True),
)

BIG_EACH = 3
NAMES = ("ab", "cd", "ef", "gh", "ij", "kl")


class Build:
    """A script under construction, with just enough state to keep it legal."""

    def __init__(self, rng, seed):
        self.rng = rng
        self.lines = ["seed %d" % seed]
        self.live = []
        self.weight = {}
        self.cfg = None
        self.saved = False

    def src(self, name, n, w, cap):
        self.lines.append("src %s %d %d %d" % (name, n, w, cap))
        self.live.append(name)
        self.weight[name] = w

    def run(self, ranks, micro, accum):
        self.cfg = (ranks, micro, accum)
        self.lines.append("run %d %d %d" % (ranks, micro, accum))

    def go(self, k):
        self.lines.append("go %d" % k)

    def save(self):
        self.lines.append("save")
        self.saved = True

    def stop(self):
        self.lines.append("stop")
        self.cfg = None

    def feed(self):
        ranks, micro, accum = self.cfg
        self.lines.append("feed %d %d" % (self.rng.randrange(ranks), self.rng.randrange(accum)))

    def at(self):
        self.lines.append("at %s" % self.rng.choice(self.live))

    def wt(self, name, w):
        self.lines.append("wt %s %d" % (name, w))
        self.weight[name] = w

    def trade(self, one, two):
        """Exchange two sources' weights, so neither the live set nor the total moves."""
        a, b = self.weight[one], self.weight[two]
        if a == b:
            return
        self.wt(one, b)
        self.wt(two, a)


def _cfg(rng, small=True):
    if small:
        return rng.choice([1, 2, 3]), rng.choice([1, 2]), rng.choice([1, 2, 3])
    return rng.choice([2, 4, 8]), rng.choice([2, 4]), rng.choice([4, 8, 16])


def _plain(rng, seed):
    b = Build(rng, seed)
    for i in range(rng.randint(2, 4)):
        b.src(NAMES[i], rng.randint(6, 40), rng.randint(1, 6), 0)
    b.run(*_cfg(rng))
    for _ in range(rng.randint(4, 9)):
        pick = rng.random()
        if pick < 0.45:
            b.go(rng.randint(1, 8))
        elif pick < 0.8:
            b.feed()
        else:
            b.at()
    return b.lines


def _roll(rng, seed):
    b = Build(rng, seed)
    for i in range(rng.randint(2, 4)):
        b.src(NAMES[i], rng.randint(1, 5), rng.randint(1, 5), 0)
    b.run(*_cfg(rng))
    for _ in range(rng.randint(5, 10)):
        pick = rng.random()
        if pick < 0.4:
            b.go(rng.randint(1, 5))
        elif pick < 0.75:
            b.feed()
        else:
            b.at()
    return b.lines


def _part(rng, seed):
    """Caps chosen so a source runs out somewhere inside a step rather than at its edge."""
    b = Build(rng, seed)
    count = rng.randint(2, 4)
    b.src(NAMES[0], rng.randint(3, 9), rng.randint(1, 5), 0)
    for i in range(1, count):
        b.src(NAMES[i], rng.randint(2, 6), rng.randint(1, 5), rng.randint(1, 4))
    b.run(*_cfg(rng))
    for _ in range(rng.randint(5, 10)):
        pick = rng.random()
        if pick < 0.5:
            b.go(rng.randint(1, 6))
        elif pick < 0.8:
            b.feed()
        else:
            b.at()
    for name in b.live:
        b.lines.append("at %s" % name)
    return b.lines


def _swap(rng, seed):
    b = Build(rng, seed)
    count = rng.randint(2, 4)
    for i in range(count):
        b.src(NAMES[i], rng.randint(4, 20), rng.randint(1, 6), 0 if i == 0 else
              rng.choice([0, 0, rng.randint(2, 6)]))
    b.run(*_cfg(rng))
    for _ in range(rng.randint(6, 11)):
        pick = rng.random()
        if pick < 0.3:
            b.go(rng.randint(1, 5))
        elif pick < 0.55:
            b.wt(rng.choice(NAMES[:count]), rng.randint(1, 6))
        elif pick < 0.85:
            b.feed()
        else:
            b.at()
    return b.lines


def _same(rng, seed):
    b = Build(rng, seed)
    count = rng.randint(2, 4)
    for i in range(count):
        b.src(NAMES[i], rng.randint(4, 24), rng.randint(1, 6), 0)
    cfg = _cfg(rng)
    b.run(*cfg)
    b.go(rng.randint(1, 4))
    b.save()
    b.go(rng.randint(1, 4))
    b.feed()
    b.stop()
    b.run(*cfg)
    for _ in range(rng.randint(3, 6)):
        pick = rng.random()
        if pick < 0.4:
            b.go(rng.randint(1, 4))
        elif pick < 0.8:
            b.feed()
        else:
            b.at()
    return b.lines


def _width(rng, seed):
    b = Build(rng, seed)
    count = rng.randint(2, 4)
    for i in range(count):
        b.src(NAMES[i], rng.randint(4, 24), rng.randint(1, 6), 0)
    b.run(*_cfg(rng))
    b.go(rng.randint(1, 4))
    b.save()
    b.go(rng.randint(0, 3))
    b.stop()
    b.run(*_cfg(rng))
    for _ in range(rng.randint(4, 8)):
        pick = rng.random()
        if pick < 0.35:
            b.go(rng.randint(1, 4))
        elif pick < 0.8:
            b.feed()
        else:
            b.at()
    return b.lines


def _late(rng, seed):
    """Something changes the blend between the checkpoint and the stop, so the counters rebase."""
    b = Build(rng, seed)
    count = rng.randint(2, 4)
    b.src(NAMES[0], rng.randint(3, 12), rng.randint(1, 5), 0)
    for i in range(1, count):
        b.src(NAMES[i], rng.randint(2, 8), rng.randint(1, 5), rng.randint(1, 3))
    b.run(*_cfg(rng))
    b.go(rng.randint(0, 2))
    b.save()
    b.go(rng.randint(1, 4))
    roll = rng.random()
    if roll < 0.35:
        b.wt(rng.choice(NAMES[:count]), rng.randint(1, 6))
    elif roll < 0.75 and count >= 2:
        # two weights traded, so neither the live set nor the weight total moves and the
        # blend is still not the one the counters were counted under
        one, two = rng.sample(NAMES[:count], 2)
        b.trade(one, two)
    b.stop()
    b.run(*_cfg(rng))
    for _ in range(rng.randint(4, 8)):
        pick = rng.random()
        if pick < 0.35:
            b.go(rng.randint(1, 4))
        elif pick < 0.8:
            b.feed()
        else:
            b.at()
    for name in b.live:
        b.lines.append("at %s" % name)
    return b.lines


def _join(rng, seed):
    b = Build(rng, seed)
    b.src(NAMES[0], rng.randint(4, 16), rng.randint(1, 5), 0)
    b.src(NAMES[1], rng.randint(4, 16), rng.randint(1, 5), 0)
    b.run(*_cfg(rng))
    b.go(rng.randint(1, 3))
    nxt = 2
    for _ in range(rng.randint(5, 9)):
        pick = rng.random()
        if pick < 0.2 and nxt < len(NAMES):
            b.src(NAMES[nxt], rng.randint(3, 14), rng.randint(1, 5),
                  rng.choice([0, rng.randint(1, 4)]))
            nxt += 1
        elif pick < 0.4:
            b.go(rng.randint(1, 3))
        elif pick < 0.5:
            b.save()
        elif pick < 0.62 and b.saved:
            b.stop()
            b.run(*_cfg(rng))
        elif pick < 0.85:
            b.feed()
        else:
            b.at()
    for name in b.live:
        b.lines.append("at %s" % name)
    return b.lines


def _big(rng, seed):
    """Millions of steps, with every capped source leaving somewhere along the run."""
    b = Build(rng, seed)
    ranks, micro, accum = rng.choice([(8, 4, 32), (4, 8, 16), (16, 2, 32), (8, 8, 16)])
    wide = ranks * micro * accum
    steps = rng.randint(1200000, 4000000)
    total = steps * wide
    count = rng.randint(3, 5)
    sizes = [rng.choice([2048, 4096, 6144, 8192]) for _ in range(count)]
    wts = [rng.randint(1, 8) for _ in range(count)]
    whole = sum(wts)
    caps = [0]
    for i in range(1, count):
        share = total * wts[i] // whole
        want = int(share * rng.uniform(0.15, 0.85))
        caps.append(max(1, want // sizes[i]))
    for i in range(count):
        b.src(NAMES[i], sizes[i], wts[i], caps[i])
    b.run(ranks, micro, accum)
    b.go(steps // 3)
    b.feed()
    b.save()
    b.go(steps // 3)
    b.at()
    if rng.random() < 0.5:
        b.wt(NAMES[rng.randrange(count)], rng.randint(1, 8))
    b.stop()
    b.run(*rng.choice([(8, 4, 32), (4, 8, 16), (2, 8, 8)]))
    b.go(steps // 3)
    b.feed()
    for name in b.live:
        b.lines.append("at %s" % name)
    return b.lines


MAKE = {
    "plain": _plain,
    "roll": _roll,
    "part": _part,
    "swap": _swap,
    "same": _same,
    "width": _width,
    "late": _late,
    "join": _join,
    "big": _big,
}


def programs(seed, per):
    """Every graded generated script, as (family, name, lines)."""
    out = []
    for fam, big in FAMILIES:
        many = BIG_EACH if big else per
        for i in range(many):
            key = hashlib.sha256(("%s|%s|%d" % (seed, fam, i)).encode("utf-8")).hexdigest()
            rng = random.Random(int(key[:16], 16))
            lines = MAKE[fam](rng, int(key[16:24], 16) % 1000000007)
            out.append((fam, "%s-%03d" % (fam, i), lines))
    return out
