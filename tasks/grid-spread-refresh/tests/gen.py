"""Deterministic script families.

Every family builds a sheet in three bands of columns and then edits it. The bands keep
the inputs inside the stated guarantee that no formula ever needs its own value:

  data columns   hold literals only;
  block columns  hold block-valued formulas, the cells their blocks occupy, and the odd
                 literal planted in the way of one. Outside the `self` family a
                 block-valued formula reads data columns only; inside it, one reads the
                 span under itself, which is legal because occupying a cell it read is
                 defined as a block that does not fit, so its value never comes from its
                 own output;
  calc columns   hold scalar formulas, which may read data cells, block-column cells
                 (occupied or not) and calc cells on earlier rows only.

The families differ in what the edit stream is aimed at:

  plain    literals and scalar formulas, so the value-level rules are exercised without
           any block in the way;
  block    blockers planted and cleared, block lengths grown and shrunk, anchors replaced
           by scalars and cleared outright;
  coin     the same, with the planted literals chosen to equal the element the block would
           have put in that cell, so a cleared blocker leaves the displayed value exactly
           where it was and a reader of it must not be recomputed;
  self     one block-valued formula per block column, reading a span of its own column
           below itself, so that a long enough block would have to occupy a cell the
           formula read;
  mix      all of the above in one stream.
"""

import random

SHAPES = ("plain", "block", "coin", "self", "mix")


def fa(t):
    return "r%dc%d" % t


class Build:
    def __init__(self, rnd, nr, nd, nb, ncalc):
        self.rnd = rnd
        self.nr = nr
        self.dc = list(range(1, nd + 1))
        self.bc = list(range(nd + 1, nd + nb + 1))
        self.cc = list(range(nd + nb + 1, nd + nb + ncalc + 1))
        self.lines = []
        self.lit = []
        self.anch = []
        self.plant = []
        self.calc = []

    def span(self):
        c0 = self.rnd.choice(self.dc)
        c1 = self.rnd.choice(self.dc)
        r0 = self.rnd.randint(1, self.nr - 2)
        r1 = min(self.nr, r0 + self.rnd.randint(1, 4))
        return "%s:%s" % (fa((r0, min(c0, c1))), fa((r1, max(c0, c1))))

    def dref(self):
        return fa((self.rnd.randint(1, self.nr), self.rnd.choice(self.dc)))

    def bref(self):
        return fa((self.rnd.randint(1, self.nr), self.rnd.choice(self.bc)))

    def scalar(self, row):
        r = self.rnd.random()
        if r < 0.28:
            return "SUM(%s)" % self.span()
        if r < 0.42:
            return "CNT(%s)" % self.span()
        if r < 0.60 and self.bc:
            return "%s + %d" % (self.bref(), self.rnd.randint(0, 4))
        if r < 0.72 and self.calc:
            other = self.rnd.choice(self.calc)
            if other[0] < row:
                return "%s + %s" % (fa(other), self.dref())
        if r < 0.86:
            a = self.bref() if self.bc and self.rnd.random() < 0.5 else self.dref()
            return "IFZ(%s, %s, %s)" % (self.dref(), a, self.dref())
        return "%s * %d - %d" % (self.dref(), self.rnd.randint(1, 3),
                                 self.rnd.randint(0, 3))

    def blocky(self, coin):
        r = self.rnd.random()
        if coin or r < 0.45:
            lo = self.rnd.randint(1, 3)
            return "RUN(%d, %d)" % (lo, lo + self.rnd.randint(0, 5))
        if r < 0.62:
            return "RUN(1, %s)" % self.dref()
        if r < 0.82:
            return "LIST(%s)" % self.span()
        return "TOP(%s, %d)" % (self.span(), self.rnd.randint(1, 5))

    def emit(self, s):
        self.lines.append(s)

    def load(self, coin, selfish=False):
        for c in self.dc:
            for r in range(1, self.nr + 1):
                if self.rnd.random() < 0.7:
                    self.lit.append((r, c))
                    self.emit("set %s %d" % (fa((r, c)), self.rnd.randint(0, 9)))
        for c in self.bc:
            if selfish:
                # One formula per column, reading the whole column under itself. The values
                # it sorts sit at the bottom, so every cell it would occupy is a cell it
                # read and empty - which is the only arrangement where occupying its own
                # input, rather than someone else's content, is what stops the block.
                top = self.rnd.randint(1, 2)
                for r in range(self.nr - 2, self.nr + 1):
                    self.plant.append((r, c))
                    self.emit("set %s %d" % (fa((r, c)), self.rnd.randint(1, 9)))
                self.anch.append((top, c))
                pick = "LIST" if self.rnd.random() < 0.35 else "TOP"
                args = "%s:%s" % (fa((top + 1, c)), fa((self.nr, c)))
                if pick == "TOP":
                    args += ", %s" % self.dref()
                self.emit("set %s = %s(%s)" % (fa((top, c)), pick, args))
                continue
            rows = sorted(self.rnd.sample(range(1, self.nr - 1), 2))
            for r in rows:
                text = self.blocky(coin)
                self.anch.append((r, c))
                self.emit("set %s = %s" % (fa((r, c)), text))
            for r in range(1, self.nr + 1):
                if (r, c) in self.anch or self.rnd.random() > 0.12:
                    continue
                self.plant.append((r, c))
                self.emit("set %s %d" % (fa((r, c)), self.coinval(r, c)))
        for c in self.cc:
            for r in range(1, self.nr + 1):
                if self.rnd.random() < 0.55:
                    self.calc.append((r, c))
                    self.emit("set %s = %s" % (fa((r, c)), self.scalar(r)))

    def coinval(self, r, c):
        """A literal that a block sitting above this cell would very likely place here."""
        best = None
        for a in self.anch:
            if a[1] == c and a[0] < r and (best is None or a[0] > best):
                best = a[0]
        if best is None:
            return self.rnd.randint(0, 9)
        return r - best + 1

    def edits(self, n, shape):
        out = []
        for _ in range(n):
            r = self.rnd.random()
            if shape == "plain":
                r = min(r, 0.42) if r < 0.72 else r
            elif shape == "self" and r < 0.66:
                r = min(r, 0.33)
            if r < 0.24 and self.lit:
                ad = self.rnd.choice(self.lit)
                out.append("set %s %d" % (fa(ad), self.rnd.randint(0, 9)))
            elif r < 0.34 and self.lit:
                out.append("clr %s" % fa(self.rnd.choice(self.lit)))
            elif r < 0.52 and self.bc:
                c = self.rnd.choice(self.bc)
                row = self.rnd.randint(1, self.nr)
                out.append("set %s %d" % (fa((row, c)), self.coinval(row, c)
                                          if shape in ("coin", "mix")
                                          else self.rnd.randint(0, 9)))
            elif r < 0.66 and self.bc:
                c = self.rnd.choice(self.bc)
                out.append("clr %s" % fa((self.rnd.randint(1, self.nr), c)))
            elif r < 0.76 and self.anch:
                ad = self.rnd.choice(self.anch)
                out.append("set %s = %s" % (fa(ad), self.blocky(shape == "coin")))
            elif r < 0.82 and self.anch:
                ad = self.rnd.choice(self.anch)
                out.append("set %s = %s" % (fa(ad), "SUM(%s)" % self.span()))
            elif r < 0.87 and self.anch:
                out.append("clr %s" % fa(self.rnd.choice(self.anch)))
            elif r < 0.95 and self.calc:
                ad = self.rnd.choice(self.calc)
                out.append("set %s = %s" % (fa(ad), self.scalar(ad[0])))
            elif self.calc:
                out.append("clr %s" % fa(self.rnd.choice(self.calc)))
            else:
                out.append("set %s %d" % (self.dref(), self.rnd.randint(0, 9)))
        return out


def one(seed, shape, nr=16, nd=3, nb=2, ncalc=4, nedit=40):
    rnd = random.Random(seed)
    if shape == "plain":
        nb = 0
    b = Build(rnd, nr, nd, nb, ncalc)
    b.load(shape == "coin", shape == "self")
    b.emit("go")
    for line in b.edits(nedit, shape):
        b.emit(line)
    return "size %d\n%s\n" % (nr, "\n".join(b.lines))


def wide(seed, nr=360, nd=26, nb=4, ncalc=60, nedit=220):
    """One large sheet, loaded cell by cell and then edited.

    The load alone is around eighteen thousand edits over a sheet that ends up carrying
    roughly twelve thousand formulas. Deciding what to bring up to date by looking at
    every formula in the sheet stays exactly correct here and does not finish.
    """
    rnd = random.Random(seed)
    b = Build(rnd, nr, nd, nb, ncalc)
    b.load(False)
    b.emit("go")
    for line in b.edits(nedit, "mix"):
        b.emit(line)
    return "size %d\n%s\n" % (nr, "\n".join(b.lines))


def batch(tag, n):
    out = []
    for shape in SHAPES:
        for i in range(n):
            out.append(("%s-%s-%03d" % (tag, shape, i),
                        one("%s|%s|%d" % (tag, shape, i), shape)))
    return out
