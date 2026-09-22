"""The graded population, generated inside the verifier from a seed drawn after the agent's
container is gone.

Shaped at each decision point rather than sampled evenly: a population that is not
deliberately built around a mechanism does not exercise it. `over` decides undo against
re-walk, `mask` decides whether a lookup that found nothing is reopened once the mask goes,
`move` decides what a lifted section entry takes with it, `gate` decides what a refused
condition leaves alone, `wake` and `late` decide the sleeping rules, `chain`, `step` and
`loop` decide the climb, and `plain` is the everyday case an overconservative resolver has to
keep working.

`wide` and `deep` are the two scale families. Neither of them is a harder reading of the
rules; they are the same rules over a journal long enough that answering every question by
walking it again does not fit the limit.
"""

import random


class Draft:
    """Collects lines, keeping track of the change numbers so `off` can name one."""

    def __init__(self):
        self.lines = []
        self.nchg = 0
        self.open = False
        self.made = []

    def entry(self, text):
        if not self.open:
            self.made.append(self.nchg)
            self.nchg += 1
        self.lines.append(text)

    def start(self):
        self.lines.append("open")
        self.made.append(self.nchg)
        self.nchg += 1
        self.open = True

    def stop(self):
        self.lines.append("shut")
        self.open = False

    def op(self, text):
        self.lines.append(text)

    def pick(self, rng):
        return rng.choice(self.made) if self.made else None


def _write(rng, names, vals=1000):
    name = rng.randrange(names)
    roll = rng.random()
    if roll < 0.62:
        return "set %d %d" % (name, rng.randrange(vals))
    if roll < 0.76:
        return "add %d %d" % (name, rng.randrange(-40, 60))
    if roll < 0.88:
        return "clr %d" % name
    return "cut %d" % name


def _guarded(rng, body, names, kind="if"):
    return "%s %d %d %s" % (kind, rng.randrange(names), rng.randrange(6), body)


def fam_plain(rng, size):
    d = Draft()
    names = max(4, size // 3)
    for _ in range(size):
        roll = rng.random()
        if roll < 0.14 and d.made:
            d.op("get 0 %d" % rng.randrange(names + 2))
        elif roll < 0.20 and d.made:
            d.op("%s %d" % ("off" if rng.random() < 0.6 else "back", d.pick(rng)))
        elif roll < 0.28:
            d.start()
            for _ in range(rng.randrange(1, 4)):
                d.entry(_write(rng, names))
            d.stop()
        else:
            d.entry(_write(rng, names))
    d.op("get 0 %d" % rng.randrange(names + 2))
    d.op("all")
    return d.lines


def fam_over(rng, size):
    """Changes that write names later changes write again, then are lifted."""
    d = Draft()
    names = 3
    for _ in range(size):
        roll = rng.random()
        if roll < 0.30 and d.made:
            d.op("%s %d" % ("off" if rng.random() < 0.55 else "back", d.pick(rng)))
        elif roll < 0.50 and d.made:
            d.op("get 0 %d" % rng.randrange(names))
        else:
            d.start()
            for _ in range(rng.randrange(1, 3)):
                d.entry(_write(rng, names))
            d.stop()
    for n in range(names):
        d.op("get 0 %d" % n)
    d.op("all")
    return d.lines


def _chain(d, depth):
    """Link section k to section k-1, all the way down to 0."""
    for sec in range(depth, 0, -1):
        d.start()
        d.entry("sec %d" % sec)
        d.entry("lnk %d" % (sec - 1))
        d.stop()
    d.entry("sec 0")


def fam_chain(rng, size):
    d = Draft()
    depth, names = 4, 6
    _chain(d, depth)
    for _ in range(size):
        roll = rng.random()
        if roll < 0.22 and d.made:
            d.op("get %d %d" % (rng.randrange(depth + 1), rng.randrange(names)))
        elif roll < 0.30 and d.made:
            d.op("%s %d" % ("off" if rng.random() < 0.6 else "back", d.pick(rng)))
        else:
            d.start()
            d.entry("sec %d" % rng.randrange(depth + 1))
            d.entry(_write(rng, names))
            d.stop()
    for sec in range(depth + 1):
        d.op("get %d %d" % (sec, rng.randrange(names)))
    d.op("all")
    return d.lines


def fam_mask(rng, size):
    """Masks in the middle of a chain, withdrawn so a climb that found nothing finds."""
    d = Draft()
    depth, names = 3, 4
    _chain(d, depth)
    d.start()
    for name in range(names):
        d.entry("set %d %d" % (name, 100 + name))
    d.stop()
    masks = []
    for _ in range(size):
        roll = rng.random()
        if roll < 0.30:
            d.start()
            d.entry("sec %d" % rng.randrange(1, depth + 1))
            d.entry("%s %d" % ("cut" if rng.random() < 0.7 else "clr", rng.randrange(names)))
            d.stop()
            masks.append(d.made[-1])
        elif roll < 0.55 and masks:
            d.op("%s %d" % ("off" if rng.random() < 0.55 else "back", rng.choice(masks)))
        else:
            d.op("get %d %d" % (rng.randrange(depth + 1), rng.randrange(names)))
    for sec in range(depth + 1):
        for name in range(names):
            d.op("get %d %d" % (sec, name))
    return d.lines


def fam_move(rng, size):
    """Section entries, some of them guarded, lifted so later writes land elsewhere."""
    d = Draft()
    secs, names = 3, 4
    moves = []
    for _ in range(size):
        roll = rng.random()
        if roll < 0.24:
            d.start()
            body = "sec %d" % rng.randrange(secs)
            d.entry(_guarded(rng, body, names) if rng.random() < 0.45 else body)
            d.stop()
            moves.append(d.made[-1])
        elif roll < 0.42 and moves:
            d.op("%s %d" % ("off" if rng.random() < 0.55 else "back", rng.choice(moves)))
        elif roll < 0.62 and d.made:
            d.op("get %d %d" % (rng.randrange(secs), rng.randrange(names)))
        else:
            d.entry(_write(rng, names))
    d.op("all")
    return d.lines


def fam_gate(rng, size):
    """`if` guards on every kind of entry, including the ones that move the walk.

    Values come from a pool of six so that a condition meets its number often, and the same
    name holds different numbers in different sections, which is what separates a condition
    read where the journal is from one read in section 0 or read without the climb.
    """
    d = Draft()
    secs, names = 3, 8
    _chain(d, 2)
    for _ in range(size):
        roll = rng.random()
        if roll < 0.18 and d.made:
            d.op("get %d %d" % (rng.randrange(secs), rng.randrange(names)))
        elif roll < 0.26 and d.made:
            d.op("%s %d" % ("off" if rng.random() < 0.6 else "back", d.pick(rng)))
        else:
            pick = rng.random()
            if pick < 0.12:
                body = "sec %d" % rng.randrange(secs)
            elif pick < 0.22:
                body = "lnk %d" % rng.randrange(secs)
            else:
                body = _write(rng, names, 6)
            d.start()
            d.entry("sec %d" % (0 if rng.random() < 0.5 else rng.randrange(1, secs)))
            d.entry(_guarded(rng, body, names) if rng.random() < 0.7 else body)
            d.stop()
    d.op("all")
    return d.lines


def fam_wake(rng, size):
    """Sleeping entries whose conditions turn each other on and off."""
    d = Draft()
    names = 4
    d.entry("set 0 1")
    for _ in range(size):
        roll = rng.random()
        if roll < 0.32:
            name = rng.randrange(names)
            body = rng.choice(["set %d %d" % (rng.randrange(names), rng.randrange(4)),
                               "clr %d" % rng.randrange(names),
                               "cut %d" % rng.randrange(names),
                               "add %d 1" % rng.randrange(names)])
            d.entry("once %d %d %s" % (name, rng.randrange(4), body))
        elif roll < 0.52 and d.made:
            d.op("get 0 %d" % rng.randrange(names))
        elif roll < 0.62 and d.made:
            d.op("%s %d" % ("off" if rng.random() < 0.6 else "back", d.pick(rng)))
        else:
            d.entry("set %d %d" % (rng.randrange(names), rng.randrange(4)))
    for name in range(names):
        d.op("get 0 %d" % name)
    d.op("all")
    return d.lines


def fam_late(rng, size):
    """Sleeping conditions read in a section an earlier entry decided.

    The same name holds different numbers in different sections here, so reading a sleeping
    condition in the section the pass ended in, or in section 0, settles on another board.
    """
    d = Draft()
    secs, names = 3, 4
    _chain(d, secs)
    for _ in range(size):
        roll = rng.random()
        if roll < 0.20:
            d.start()
            d.entry("sec %d" % rng.randrange(secs + 1))
            d.entry("once %d %d %s" % (rng.randrange(names), rng.randrange(4),
                                       _write(rng, names, 4)))
            d.stop()
        elif roll < 0.34:
            d.start()
            d.entry("sec %d" % rng.randrange(secs + 1))
            d.entry("once %d %d sec %d" % (rng.randrange(names), rng.randrange(4),
                                           rng.randrange(secs + 1)))
            d.stop()
        elif roll < 0.54 and d.made:
            d.op("get %d %d" % (rng.randrange(secs + 1), rng.randrange(names)))
        elif roll < 0.64 and d.made:
            d.op("%s %d" % ("off" if rng.random() < 0.6 else "back", d.pick(rng)))
        else:
            d.entry(_write(rng, names, 4))
    d.op("all")
    return d.lines


def fam_step(rng, size):
    """`add` reading through a chain, over names that come and go."""
    d = Draft()
    depth, names = 3, 4
    _chain(d, depth)
    d.start()
    for name in range(names):
        d.entry("set %d %d" % (name, 10 * name))
    d.stop()
    for _ in range(size):
        roll = rng.random()
        if roll < 0.40:
            d.start()
            d.entry("sec %d" % rng.randrange(depth + 1))
            d.entry("add %d %d" % (rng.randrange(names), rng.randrange(-20, 30)))
            d.stop()
        elif roll < 0.55:
            d.start()
            d.entry("sec %d" % rng.randrange(depth + 1))
            d.entry("%s %d" % (rng.choice(["clr", "cut"]), rng.randrange(names)))
            d.stop()
        elif roll < 0.75 and d.made:
            d.op("get %d %d" % (rng.randrange(depth + 1), rng.randrange(names)))
        else:
            d.op("%s %d" % ("off" if rng.random() < 0.6 else "back", d.pick(rng)))
    for sec in range(depth + 1):
        for name in range(names):
            d.op("get %d %d" % (sec, name))
    return d.lines


def fam_loop(rng, size):
    """Links that come back round, including a section linked to itself."""
    d = Draft()
    secs, names = 4, 4
    for _ in range(size):
        roll = rng.random()
        if roll < 0.28:
            d.start()
            d.entry("sec %d" % rng.randrange(secs))
            d.entry("lnk %d" % rng.randrange(secs))
            d.stop()
        elif roll < 0.48 and d.made:
            d.op("get %d %d" % (rng.randrange(secs), rng.randrange(names)))
        elif roll < 0.60 and d.made:
            d.op("%s %d" % ("off" if rng.random() < 0.6 else "back", d.pick(rng)))
        else:
            d.start()
            d.entry("sec %d" % rng.randrange(secs))
            d.entry(_write(rng, names))
            d.stop()
    for sec in range(secs):
        for name in range(names):
            d.op("get %d %d" % (sec, name))
    d.op("all")
    return d.lines


def fam_wide(rng, size):
    """Scale: a long journal answering many questions, with the changes spread over names."""
    d = Draft()
    names = max(64, size // 12)
    holds = []
    for step in range(size):
        roll = rng.random()
        if roll < 0.10 and d.made:
            d.op("%s %d" % ("off" if rng.random() < 0.55 else "back", d.pick(rng)))
        elif roll < 0.48 and d.made:
            d.op("get 0 %d" % rng.randrange(names))
        elif roll < 0.485 and step > size // 2:
            d.entry("once %d %d set %d %d"
                    % (rng.randrange(names), rng.randrange(1000),
                       rng.randrange(names), rng.randrange(1000)))
            holds.append(d.made[-1])
        else:
            d.entry(_write(rng, names))
    for _ in range(12):
        d.op("get 0 %d" % rng.randrange(names))
    d.op("all")
    return d.lines


def fam_deep(rng, size):
    """Scale: the same length again, with every read climbing a chain six sections deep."""
    d = Draft()
    depth = 6
    names = max(48, size // 16)
    _chain(d, depth)
    for _ in range(size):
        roll = rng.random()
        if roll < 0.10 and d.made:
            d.op("%s %d" % ("off" if rng.random() < 0.55 else "back", d.pick(rng)))
        elif roll < 0.62:
            d.op("get %d %d" % (depth, rng.randrange(names)))
        else:
            d.start()
            d.entry("sec %d" % rng.randrange(depth + 1))
            d.entry(_write(rng, names))
            d.stop()
    for _ in range(12):
        d.op("get %d %d" % (depth, rng.randrange(names)))
    return d.lines


SMALL = (
    ("plain", fam_plain),
    ("over", fam_over),
    ("chain", fam_chain),
    ("mask", fam_mask),
    ("move", fam_move),
    ("gate", fam_gate),
    ("wake", fam_wake),
    ("late", fam_late),
    ("step", fam_step),
    ("loop", fam_loop),
)
BIG = (
    ("wide", fam_wide),
    ("deep", fam_deep),
)
FAMILIES = tuple(name for name, _fn in SMALL) + tuple(name for name, _fn in BIG)

BIG_SIZE = 30000
BIG_EACH = 3


def programs(seed, per):
    """Every graded program that is not one of the enumerated hand ones."""
    out = []
    for name, fn in SMALL:
        for k in range(per):
            rng = random.Random("%s/%s/%d" % (seed, name, k))
            out.append((name, "%s-%02d" % (name, k), fn(rng, 34 + (k % 6) * 13)))
    for name, fn in BIG:
        for k in range(BIG_EACH):
            rng = random.Random("%s/%s/%d" % (seed, name, k))
            out.append((name, "%s-%d" % (name, k), fn(rng, BIG_SIZE)))
    return out
