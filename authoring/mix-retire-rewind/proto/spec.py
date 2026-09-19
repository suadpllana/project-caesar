"""Prototype of the feeder semantics, in two implementations.

`Walk` fills one slot at a time and is obviously right; it is the naive family the resource
gate has to kill. `Jump` derives the feeder's state at an arbitrary slot and is the shape the
reference will take. Both are here so the differential test and the timing run happen before
the design depends on either.

Semantics, as they will be frozen:

  * A run consumes the stream in steps of world * micro * accum slots.
  * Slot i of a segment that began at slot a takes its source from pat[(i - a) % len(pat)].
  * A source hands over its samples in the order perm(seed, sid, epoch); a sample whose token
    length is over the cap is passed over, advances the cursor, and the same source is asked
    again, crossing into the next epoch if the cursor runs off the end.
  * A source with an allowance retires the moment it delivers the last sample its allowance
    covers - its within-cap count times the allowance. Its entries leave the pattern and the
    next slot begins a new segment.
"""

M64 = (1 << 64) - 1


def perm(seed, sid, ep, n):
    """The order source `sid` hands its samples over in, for one epoch."""
    x = (seed * 6364136223846793005 + (sid + 1) * 1442695040888963407
         + ep * 2862933555777941757 + 1) & M64
    x = x or 1
    out = list(range(n))
    for i in range(n - 1, 0, -1):
        x ^= (x << 13) & M64
        x &= M64
        x ^= x >> 7
        x ^= (x << 17) & M64
        x &= M64
        out[i], out[x % (i + 1)] = out[x % (i + 1)], out[i]
    return out


class Cfg:
    def __init__(self, seed, cap, names, lens, allow, mix):
        self.seed = seed
        self.cap = cap
        self.names = names
        self.lens = lens
        self.allow = allow
        self.mix = mix                      # list of source ids
        self.good = [sum(1 for v in ls if v <= cap) for ls in lens]
        self.n = [len(ls) for ls in lens]


# --------------------------------------------------------------------------- naive

class Walk:
    """One slot at a time, keeping cursors as it goes."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.pat = list(cfg.mix)
        self.base = 0                        # first slot of the live segment
        self.slot = 0
        k = len(cfg.lens)
        self.cur = [0] * k
        self.ep = [0] * k
        self.took = [0] * k
        self.gone = [False] * k
        self.cache = {}

    def order(self, j, e):
        got = self.cache.get(j)
        if got is None or got[0] != e:
            got = (e, perm(self.cfg.seed, j, e, self.cfg.n[j]))
            self.cache[j] = got
        return got[1]

    def one(self):
        cfg = self.cfg
        j = self.pat[(self.slot - self.base) % len(self.pat)]
        while True:
            x = self.order(j, self.ep[j])[self.cur[j]]
            self.cur[j] += 1
            if self.cur[j] == cfg.n[j]:
                self.cur[j] = 0
                self.ep[j] += 1
            if cfg.lens[j][x] <= cfg.cap:
                break
        self.took[j] += 1
        self.slot += 1
        if cfg.allow[j] and self.took[j] == cfg.good[j] * cfg.allow[j]:
            self.gone[j] = True
            self.pat = [s for s in self.pat if s != j]
            self.base = self.slot
        return (j, x)

    def upto(self, slot):
        while self.slot < slot:
            self.one()

    def slots(self, at, count):
        self.upto(at)
        return [self.one() for _ in range(count)]

    def state(self, slot):
        self.upto(slot)
        return [("gone",) if self.gone[j] else (self.ep[j], self.cur[j], self.took[j])
                for j in range(len(self.cfg.lens))]


# --------------------------------------------------------------------------- derived

class Jump:
    """The feeder's state at a slot, worked out rather than walked to.

    Two facts carry it. A permutation does not change a multiset, so every epoch of a source
    delivers the same number of samples, which turns a delivered count into an epoch and a
    position inside one. And between two retirements the pattern is fixed, so the count of a
    source over a stretch of slots is periodic in the pattern's length.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.k = len(cfg.lens)
        self.cache = {}
        self.segs = [(0, tuple(cfg.mix), tuple([0] * self.k))]
        self.closed = False                  # the last segment runs forever

    # -- per source -------------------------------------------------------

    def acc(self, j, e):
        """Positions of the within-cap samples of one epoch, in hand-over order."""
        got = self.cache.get((j, e))
        if got is None:
            cfg = self.cfg
            order = perm(cfg.seed, j, e, cfg.n[j])
            got = ([i for i, x in enumerate(order) if cfg.lens[j][x] <= cfg.cap], order)
            if len(self.cache) > 64:
                self.cache.clear()
            self.cache[(j, e)] = got
        return got

    def where(self, j, took):
        """(epoch, cursor) of source j once it has delivered `took` samples."""
        if took == 0:
            return (0, 0)
        g = self.cfg.good[j]
        e, r = (took - 1) // g, (took - 1) % g
        at = self.acc(j, e)[0][r] + 1
        if at == self.cfg.n[j]:
            return (e + 1, 0)
        return (e, at)

    def sample(self, j, took):
        """The sample id source j hands over as its (took+1)-th delivery."""
        g = self.cfg.good[j]
        e, r = took // g, took % g
        got, order = self.acc(j, e)
        return order[got[r]]

    # -- the segment timeline ---------------------------------------------

    @staticmethod
    def spots(pat, j):
        return [i for i, s in enumerate(pat) if s == j]

    @classmethod
    def count(cls, pat, j, width):
        """How many of the first `width` slots of a segment belong to source j."""
        per = pat.count(j)
        if not per:
            return 0
        whole, rest = divmod(width, len(pat))
        return whole * per + sum(1 for i in range(rest) if pat[i] == j)

    def grow(self, slot):
        """Extend the timeline until the segment holding `slot` is known."""
        while not self.closed and self.segs[-1][0] <= slot:
            start, pat, took = self.segs[-1]
            best = None
            for j in set(pat):
                if not self.cfg.allow[j]:
                    continue
                left = self.cfg.good[j] * self.cfg.allow[j] - took[j]
                per = pat.count(j)
                whole, rest = divmod(left - 1, per)
                at = whole * len(pat) + self.spots(pat, j)[rest]
                if best is None or at < best[0]:
                    best = (at, j)
            if best is None:
                self.closed = True
                break
            at, j = best
            nxt = tuple(took[i] + self.count(pat, i, at + 1) for i in range(self.k))
            self.segs.append((start + at + 1, tuple(s for s in pat if s != j), nxt))
            if self.segs[-1][0] > slot:
                break

    def seg(self, slot):
        self.grow(slot)
        lo = 0
        for i, (start, _p, _t) in enumerate(self.segs):
            if start <= slot:
                lo = i
        return self.segs[lo]

    def took(self, slot):
        """Every source's delivered count at `slot`, before that slot is filled."""
        start, pat, took = self.seg(slot)
        return [took[j] + self.count(pat, j, slot - start) for j in range(self.k)]

    def state(self, slot):
        took = self.took(slot)
        out = []
        for j in range(self.k):
            done = self.cfg.allow[j] and took[j] >= self.cfg.good[j] * self.cfg.allow[j]
            if done:
                out.append(("gone",))
            else:
                e, c = self.where(j, took[j])
                out.append((e, c, took[j]))
        return out

    def slots(self, at, count):
        took = self.took(at)
        out = []
        slot = at
        while len(out) < count:
            start, pat, _t = self.seg(slot)
            j = pat[(slot - start) % len(pat)]
            out.append((j, self.sample(j, took[j])))
            took[j] += 1
            slot += 1
        return out


def deal(world, micro, accum, pairs):
    """Slot offset o inside a step goes to rank o % world; each rank's slots fill its
    accumulation micro-batches in order."""
    out = [[[] for _ in range(accum)] for _ in range(world)]
    for o, pair in enumerate(pairs):
        r = o % world
        seat = o // world
        out[r][seat // micro].append(pair)
    return out
