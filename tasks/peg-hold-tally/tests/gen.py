"""Programs generated inside the verifier, from a seed drawn after the agent's container is gone.

Nine families. Six of them are small and each is a shape rather than a size: `weave` holds one
block at several slots of one volume, `hop` takes blocks back into volumes they had left, `braid`
forks and lets the forks diverge, `prune` sheds pegs in every order, `plain` is ordinary traffic
and `mix` does all of it at once. A wrong reading of any graded decision moves at least one printed
line in at least one of them.

The last three are the large ones and they are what the execution limit is about. `wide` keeps a
large volume under a long working period with pegs standing over it; `crop` keeps a rolling window
of pegs over a large volume and sheds the oldest as it goes; `fan` forks a filled volume many times
and lets every fork diverge. Nothing in them is new: they are the small shapes at the size a real
store runs at.
"""
import random

OPS = ("set", "clr", "dup", "peg", "shed", "fork", "back", "trim", "tally")

WEIGHTS = {
    "plain": {"set": 40, "clr": 12, "dup": 0, "peg": 14, "shed": 10, "fork": 0,
              "back": 0, "trim": 10, "tally": 14},
    "weave": {"set": 26, "clr": 14, "dup": 24, "peg": 12, "shed": 8, "fork": 0,
              "back": 0, "trim": 8, "tally": 8},
    "hop": {"set": 26, "clr": 14, "dup": 6, "peg": 16, "shed": 8, "fork": 0,
            "back": 14, "trim": 8, "tally": 8},
    "braid": {"set": 26, "clr": 10, "dup": 4, "peg": 16, "shed": 8, "fork": 10,
              "back": 6, "trim": 8, "tally": 12},
    "prune": {"set": 24, "clr": 12, "dup": 4, "peg": 22, "shed": 18, "fork": 2,
              "back": 4, "trim": 6, "tally": 8},
    "mix": {"set": 24, "clr": 10, "dup": 10, "peg": 14, "shed": 10, "fork": 6,
            "back": 10, "trim": 7, "tally": 9},
}

SMALL = ("plain", "weave", "hop", "braid", "prune", "mix")
BIG = ("wide", "crop", "fan")
FAMILIES = tuple((f, True) for f in SMALL) + tuple((f, False) for f in BIG)

SHAPES = ((40, 4, 1), (60, 6, 2), (90, 8, 2), (120, 5, 3), (200, 10, 3), (70, 3, 1))


class Maker:
    """One small program: legal by construction, and never naming a peg that has been shed."""

    def __init__(self, rng, slots, vols):
        self.rng = rng
        self.slots = slots
        self.vols = ["v%d" % i for i in range(1, vols + 1)]
        self.full = {v: set() for v in self.vols}
        self.pegs = []
        self.hint = {}
        self.snap = {}
        self.np = 0
        self.nv = vols
        self.lines = ["vol %s" % v for v in self.vols]

    def pick(self, seq):
        return self.rng.choice(seq) if seq else None

    def slot(self):
        return str(self.rng.randrange(self.slots))

    def step(self, w):
        kind = self.rng.choices(OPS, weights=[w[k] for k in OPS])[0]
        v = self.pick(self.vols)
        if kind == "set":
            x = self.slot()
            self.full[v].add(x)
            return "set %s %s" % (v, x)
        if kind == "clr":
            x = self.pick(sorted(self.full[v]))
            if x is None:
                return None
            self.full[v].discard(x)
            return "clr %s %s" % (v, x)
        if kind == "dup":
            s = self.pick(sorted(self.full[v]))
            if s is None:
                return None
            d = self.slot()
            if d == s:
                return None
            self.full[v].add(d)
            return "dup %s %s %s" % (v, d, s)
        if kind == "peg":
            self.np += 1
            p = "p%d" % self.np
            self.pegs.append((p, v))
            here = sorted(self.full[v])
            self.snap[p] = set(here)
            self.rng.shuffle(here)
            self.hint[p] = here[:8]
            return "peg %s %s" % (p, v)
        if kind == "shed":
            got = self.pick(self.pegs)
            if got is None:
                return None
            self.pegs.remove(got)
            self.hint.pop(got[0], None)
            self.snap.pop(got[0], None)
            return "shed %s" % got[0]
        if kind == "fork":
            got = self.pick(self.pegs)
            if got is None:
                return None
            self.nv += 1
            w2 = "v%d" % self.nv
            self.vols.append(w2)
            self.full[w2] = set(self.snap[got[0]])
            return "fork %s %s" % (w2, got[0])
        if kind == "back":
            got = self.pick(self.pegs)
            if got is None:
                return None
            y = self.pick(self.hint.get(got[0], []))
            if y is None:
                return None
            if self.rng.random() < 0.45:
                return self.gap(got, y)
            x = self.slot()
            self.full[v].add(x)
            return "back %s %s %s %s" % (v, x, got[0], y)
        if kind == "trim":
            return "trim"
        if kind == "tally":
            got = self.pick(self.pegs)
            return None if got is None else "tally %s" % got[0]
        return None

    def gap(self, got, y):
        """Send a block away from its own volume, peg while it is away, and bring that same one back.

        A peg made while a block is away from a volume keeps nothing of it. An unshaped stream
        almost never produces the four steps that separate that from reading the hold as one
        stretch - the block has to leave, a peg has to be made, the same block has to come back,
        and the pegs that do keep it have to go - so the shape is generated rather than waited for.
        """
        _p, v = got
        y = self.pick(sorted(self.full[v]))
        if y is None:
            return None
        out = []
        first = self.peg_at(v)
        out.append("peg %s %s" % (first, v))
        self.full[v].discard(y)
        out.append("clr %s %s" % (v, y))
        out.append("peg %s %s" % (self.peg_at(v), v))
        self.full[v].add(y)
        out.append("back %s %s %s %s" % (v, y, first, y))
        if self.rng.random() < 0.75:
            self.full[v].discard(y)
            out.append("clr %s %s" % (v, y))
        if self.rng.random() < 0.6:
            self.pegs = [g for g in self.pegs if g[0] != first]
            self.hint.pop(first, None)
            self.snap.pop(first, None)
            out.append("shed %s" % first)
            out.append("trim")
        return out

    def peg_at(self, v):
        """Make a peg over v now, remembering what it holds the way a `peg` op would."""
        self.np += 1
        p = "p%d" % self.np
        self.pegs.append((p, v))
        here = sorted(self.full[v])
        self.snap[p] = set(here)
        self.rng.shuffle(here)
        self.hint[p] = here[:8]
        return p

    def run(self, w, n):
        while len(self.lines) < n:
            line = self.step(w)
            if isinstance(line, list):
                self.lines.extend(line)
            elif line is not None:
                self.lines.append(line)
        if self.lines[-1] != "trim":
            self.lines.append("trim")
        return self.lines


def small(fam, seed, n, slots, vols):
    return Maker(random.Random(str(seed)), slots, vols).run(WEIGHTS[fam], n)


def wide(seed, slots=24000, ops=90000):
    """One large volume, pegs standing over a long working period, blocks taken back into it."""
    rng = random.Random(str(seed))
    out = ["vol v1"]
    for x in range(slots):
        out.append("set v1 %d" % x)
    live = []
    np = 0
    for i in range(ops):
        r = rng.random()
        if r < 0.62:
            out.append("set v1 %d" % rng.randrange(slots))
        elif r < 0.74:
            out.append("clr v1 %d" % rng.randrange(slots))
        elif r < 0.84:
            d, s = rng.randrange(slots), rng.randrange(slots)
            if d != s:
                out.append("dup v1 %d %d" % (d, s))
        elif r < 0.92 and live:
            out.append("back v1 %d %s %d" % (
                rng.randrange(slots), rng.choice(live), rng.randrange(slots)))
        else:
            out.append("set v1 %d" % rng.randrange(slots))
        if i % 70 == 0:
            np += 1
            live.append("p%d" % np)
            out.append("peg p%d v1" % np)
        if i % 900 == 0 and len(live) > 20:
            out.append("shed %s" % live.pop(rng.randrange(len(live) // 2)))
        if i % 260 == 0:
            out.append("trim")
        if i % 90 == 0 and live:
            out.append("tally %s" % rng.choice(live))
    out.append("trim")
    return out


def crop(seed, slots=45000, ops=180000, window=220):
    """Two large volumes under a rolling window of pegs: the oldest is shed as new ones are made."""
    rng = random.Random(str(seed))
    out = ["vol v1", "vol v2"]
    for x in range(slots):
        out.append("set v1 %d" % x)
    for x in range(slots // 4):
        out.append("set v2 %d" % x)
    live = []
    np = 0
    for i in range(ops):
        v = "v1" if rng.random() < 0.75 else "v2"
        top = slots if v == "v1" else slots // 4
        r = rng.random()
        if r < 0.62:
            out.append("set %s %d" % (v, rng.randrange(top)))
        elif r < 0.74:
            out.append("clr %s %d" % (v, rng.randrange(top)))
        elif r < 0.84:
            d, s = rng.randrange(top), rng.randrange(top)
            if d != s:
                out.append("dup %s %d %d" % (v, d, s))
        elif r < 0.90 and live:
            out.append("back %s %d %s %d" % (
                v, rng.randrange(top), rng.choice(live), rng.randrange(top)))
        else:
            out.append("set %s %d" % (v, rng.randrange(top)))
        if i % 9 == 0:
            np += 1
            live.append("p%d" % np)
            out.append("peg p%d %s" % (np, v))
        if len(live) > window:
            out.append("shed %s" % live.pop(0))
        if i % 240 == 0:
            out.append("trim")
        if i % 70 == 0 and live:
            out.append("tally %s" % rng.choice(live))
    out.append("trim")
    return out


def fan(seed, slots=5000, forks=30, ops=70000):
    """A filled volume forked many times, with every fork diverging afterwards."""
    rng = random.Random(str(seed))
    out = ["vol v1"]
    for x in range(slots):
        out.append("set v1 %d" % x)
    vols = ["v1"]
    live = []
    np = nv = 0
    for _k in range(forks):
        np += 1
        out.append("peg p%d %s" % (np, rng.choice(vols)))
        live.append("p%d" % np)
        nv += 1
        out.append("fork w%d p%d" % (nv, np))
        vols.append("w%d" % nv)
        for _ in range(60):
            out.append("set %s %d" % (rng.choice(vols), rng.randrange(slots)))
    for i in range(ops):
        v = rng.choice(vols)
        r = rng.random()
        if r < 0.58:
            out.append("set %s %d" % (v, rng.randrange(slots)))
        elif r < 0.72:
            out.append("clr %s %d" % (v, rng.randrange(slots)))
        elif r < 0.82:
            d, s = rng.randrange(slots), rng.randrange(slots)
            if d != s:
                out.append("dup %s %d %d" % (v, d, s))
        elif r < 0.90 and live:
            out.append("back %s %d %s %d" % (
                v, rng.randrange(slots), rng.choice(live), rng.randrange(slots)))
        else:
            out.append("set %s %d" % (v, rng.randrange(slots)))
        if i % 55 == 0:
            np += 1
            out.append("peg p%d %s" % (np, rng.choice(vols)))
            live.append("p%d" % np)
        if i % 600 == 0 and len(live) > 15:
            out.append("shed %s" % live.pop(rng.randrange(len(live) // 2)))
        if i % 250 == 0:
            out.append("trim")
        if i % 85 == 0 and live:
            out.append("tally %s" % rng.choice(live))
    out.append("trim")
    return out


BIGMAKE = {"wide": wide, "crop": crop, "fan": fan}


def programs(seed, per):
    """The graded population: `per` of each small family, three of each large one."""
    out = []
    for fam in SMALL:
        for i in range(per):
            n, slots, vols = SHAPES[i % len(SHAPES)]
            if fam in ("plain", "weave", "hop"):
                vols = min(vols, 2)
            name = "%s-%d" % (fam, i)
            out.append((fam, name, small(fam, "%s-%s" % (seed, name), n, slots, vols)))
    for fam in BIG:
        for i in range(3):
            name = "%s-%d" % (fam, i)
            out.append((fam, name, BIGMAKE[fam]("%s-%s" % (seed, name))))
    return out
