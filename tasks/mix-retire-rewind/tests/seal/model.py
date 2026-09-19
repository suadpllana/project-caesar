"""The sealed feeder. Written apart from the reference, and the definition of correct.

It answers one question - what does this plan print - and it answers it by a different route
from `solution/`:

  * the stretch timeline is built eagerly into three parallel lists and looked up with
    `bisect`, where the reference grows a lazy dict and finds a stretch by its own descent;
  * each retirement slot is found by doubling and then bisecting the monotone count of a
    source's slots, where the reference solves for it in closed form - so an off-by-one in
    either shows up as a disagreement rather than as agreement on a shared mistake;
  * a source's position inside an epoch is found by counting forward through the hand-over
    order with an early exit, where the reference precomputes the list of within-cap places;
  * only the slots a printed line actually names are worked out, each from the timeline with
    no carried state, where the reference fills a whole step from a running count;
  * the offsets a micro-batch is made of come straight out of the deal formula, where the
    reference deals a whole step into buckets and indexes them.

The hand-over order is the one frozen in the environment, copied here so the sealed side does
not import anything the agent could have replaced.
"""
import bisect

M = (1 << 64) - 1


def hand(seed, sid, ep, n):
    x = (seed * 6364136223846793005 + (sid + 1) * 1442695040888963407
         + ep * 2862933555777941757 + 1) & M or 1
    out = list(range(n))
    for i in range(n - 1, 0, -1):
        x ^= (x << 13) & M
        x &= M
        x ^= x >> 7
        x ^= (x << 17) & M
        x &= M
        j = x % (i + 1)
        out[i], out[j] = out[j], out[i]
    return out


def tally(pat, j, wide):
    """How many of the first `wide` slots of a stretch belong to source j."""
    whole, rest = divmod(wide, len(pat))
    return whole * pat.count(j) + pat[:rest].count(j)


class Feed:
    def __init__(self):
        self.seed = 0
        self.cap = 0
        self.names = []
        self.lens = []
        self.hold = []
        self.pat = []
        self.runs = {}
        self.marks = {}
        self.out = []
        self.orders = {}
        self.fit = {}
        self.starts = None
        self.pats = None
        self.counts = None
        self.more = True

    # -- one source ----------------------------------------------------------

    def fits(self, j):
        got = self.fit.get(j)
        if got is None:
            got = sum(1 for v in self.lens[j] if v <= self.cap)
            self.fit[j] = got
        return got

    def order(self, j, ep):
        got = self.orders.get((j, ep))
        if got is None:
            got = hand(self.seed, j, ep, len(self.lens[j]))
            if len(self.orders) > 300:
                self.orders.clear()
            self.orders[(j, ep)] = got
        return got

    def nth(self, j, ep, r):
        """(place in the hand-over order, sample) of the r-th within-cap sample of an epoch."""
        lens = self.lens[j]
        seen = -1
        for i, x in enumerate(self.order(j, ep)):
            if lens[x] <= self.cap:
                seen += 1
                if seen == r:
                    return i, x
        raise AssertionError("epoch %d of source %d has no sample %d inside the cap"
                             % (ep, j, r))

    def gives(self, j, took):
        """The sample source j hands over as its delivery numbered `took`, counting from 0."""
        ep, r = divmod(took, self.fits(j))
        return self.nth(j, ep, r)[1]

    def stands(self, j, took):
        """(epoch, cursor) of source j once it has delivered `took` samples."""
        if took == 0:
            return 0, 0
        ep, r = divmod(took - 1, self.fits(j))
        place = self.nth(j, ep, r)[0] + 1
        if place == len(self.lens[j]):
            return ep + 1, 0
        return ep, place

    def spent(self, j, took):
        return bool(self.hold[j]) and took >= self.fits(j) * self.hold[j]

    # -- the stretch timeline ------------------------------------------------

    def begin(self):
        if self.starts is None:
            self.starts = [0]
            self.pats = [list(self.pat)]
            self.counts = [[0] * len(self.lens)]
            self.more = True

    def grow(self, slot):
        self.begin()
        while self.more and self.starts[-1] <= slot:
            pat, took = self.pats[-1], self.counts[-1]
            leaving = []
            for j in sorted(set(pat)):
                if not self.hold[j]:
                    continue
                need = self.fits(j) * self.hold[j] - took[j]
                hi = 1
                while tally(pat, j, hi + 1) < need:
                    hi *= 2
                lo = 0
                while lo < hi:
                    mid = (lo + hi) // 2
                    if tally(pat, j, mid + 1) >= need:
                        hi = mid
                    else:
                        lo = mid + 1
                leaving.append((lo, j))
            if not leaving:
                self.more = False
                return
            at, j = min(leaving)
            self.starts.append(self.starts[-1] + at + 1)
            self.pats.append([s for s in pat if s != j])
            self.counts.append([took[i] + tally(pat, i, at + 1)
                                for i in range(len(self.lens))])

    def stretch(self, slot):
        self.grow(slot)
        return bisect.bisect_right(self.starts, slot) - 1

    def owner(self, slot):
        i = self.stretch(slot)
        pat = self.pats[i]
        return pat[(slot - self.starts[i]) % len(pat)]

    def delivered(self, slot):
        """Every source's delivered count as the slot is about to be filled."""
        i = self.stretch(slot)
        pat, base = self.pats[i], self.counts[i]
        wide = slot - self.starts[i]
        return [base[j] + tally(pat, j, wide) for j in range(len(self.lens))]

    def sample(self, slot):
        j = self.owner(slot)
        return j, self.gives(j, self.delivered(slot)[j])

    def where(self, slot):
        took = self.delivered(slot)
        out = []
        for j in range(len(self.lens)):
            if self.spent(j, took[j]):
                out.append(None)
            else:
                ep, cur = self.stands(j, took[j])
                out.append((ep, cur, took[j]))
        return out

    # -- the printed lines ---------------------------------------------------

    def stand_text(self, seen):
        out = []
        for j, one in enumerate(seen):
            if one is None:
                out.append("%s:gone" % self.names[j])
            else:
                out.append("%s:%d:%d:%d" % (self.names[j], one[0], one[1], one[2]))
        return " ".join(out)

    def fresh(self):
        """Any change to the corpus or the mix throws the timeline and the caches away."""
        self.orders.clear()
        self.fit.clear()
        self.starts = None
        self.pats = None
        self.counts = None
        self.more = True

    def ex(self, w):
        op = w[0]
        if op == "seed":
            self.seed = int(w[1])
            self.fresh()
        elif op == "cap":
            self.cap = int(w[1])
            self.fresh()
        elif op == "src":
            self.names.append(w[1])
            self.hold.append(int(w[2]))
            self.lens.append([int(v) for v in w[3].split(",")])
            self.fresh()
        elif op == "mix":
            self.pat = [self.names.index(name) for name in w[1:]]
            self.fresh()
        elif op == "open":
            self.runs[w[1]] = {"base": 0, "done": 0, "made": 0,
                               "w": int(w[2]), "m": int(w[3]), "a": int(w[4])}
        elif op == "feed":
            self.runs[w[1]]["made"] += int(w[2])
        elif op == "take":
            run = self.runs[w[1]]
            run["done"] += int(w[2])
            run["made"] = max(run["made"], run["done"])
        elif op == "show":
            run = self.runs[w[1]]
            step, rank, seat = int(w[2]), int(w[3]), int(w[4])
            world, micro, accum = run["w"], run["m"], run["a"]
            head = run["base"] + step * world * micro * accum
            got = []
            for p in range(micro):
                slot = head + (seat * micro + p) * world + rank
                j, x = self.sample(slot)
                got.append("%s.%d" % (self.names[j], x))
            self.out.append("show %s %d %d %d %s"
                            % (w[1], step, rank, seat, " ".join(got)))
        elif op == "save":
            run = self.runs[w[1]]
            wide = run["w"] * run["m"] * run["a"]
            rec = {"base": run["base"], "done": run["done"], "made": run["made"],
                   "wide": wide}
            self.marks[w[2]] = rec
            self.out.append("save %s %d %d %d %s"
                            % (w[2], rec["base"], rec["done"], rec["made"],
                               self.stand_text(self.where(run["base"] + run["made"] * wide))))
        elif op == "load":
            rec = self.marks[w[2]]
            base = rec["base"] + rec["done"] * rec["wide"]
            self.runs[w[1]] = {"base": base, "done": 0, "made": 0,
                               "w": int(w[3]), "m": int(w[4]), "a": int(w[5])}
            self.out.append("load %s %d %s" % (w[1], base, self.stand_text(self.where(base))))
        else:
            raise AssertionError("unknown op %r" % (op,))


def expect(lines):
    feed = Feed()
    for line in lines:
        line = line.strip()
        if line:
            feed.ex(tuple(line.split()))
    return feed.out
