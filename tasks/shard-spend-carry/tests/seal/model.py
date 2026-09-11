"""The sealed model: a second implementation of the contract, written apart from the reference.

The reference holds a parameter as one list of [count, value, moment, pending] rows and indexes
the parameters that still carry pending work by their position in the map. This holds a
parameter as two parallel lists - the offset each run starts at, and its three numbers - and
indexes pending work by the flat offset each such parameter ends at, so a rank finds its first
payable parameter by bisecting end offsets rather than map positions. Neither shares code with
the other, and they were written to the same brief rather than to each other.

`expect(lines)` returns the trace a correct engine prints for one program.
"""
from bisect import bisect_left, bisect_right
from itertools import accumulate


class Par:
    __slots__ = ("n", "at", "st", "live", "born", "mapped", "owed")

    def __init__(self, n, born):
        self.n = n
        self.at = [0]
        self.st = [[0, 0, 0]]
        self.live = True
        self.born = born
        self.mapped = False
        self.owed = False

    def tidy(self):
        at, st = [self.at[0]], [self.st[0]]
        for i in range(1, len(self.at)):
            if self.st[i] != st[-1]:
                at.append(self.at[i])
                st.append(self.st[i])
        self.at, self.st = at, st
        self.owed = any(x[2] for x in st)

    def split(self, k):
        """Make sure a run starts exactly at offset k, and return its index."""
        i = bisect_right(self.at, k) - 1
        if self.at[i] == k:
            return i
        self.at.insert(i + 1, k)
        self.st.insert(i + 1, list(self.st[i]))
        return i + 1

    def feed(self, k):
        for x in self.st:
            x[2] += k
        self.tidy()

    def forget(self):
        for x in self.st:
            x[1] = 0
        self.tidy()

    def show(self, f):
        out = []
        for i, x in enumerate(self.st):
            wide = (self.at[i + 1] if i + 1 < len(self.at) else self.n) - self.at[i]
            out.append((wide, x[f]))
        return out

    def pay(self, lo, hi, purse):
        """Spend `purse` on slots [lo,hi); returns what was spent and whether it ran out."""
        used = 0
        stop = False
        i = self.split(lo)
        while i < len(self.st):
            here = self.at[i]
            if here >= hi:
                break
            end = self.at[i + 1] if i + 1 < len(self.at) else self.n
            if end > hi:
                self.split(hi)
                end = hi
            g = self.st[i][2]
            if g:
                unit = -g if g < 0 else g
                room = (purse - used) // unit
                wide = end - here
                if room < wide:
                    if room:
                        self.split(here + room)
                    stop = True
                    wide = room
                if wide:
                    used += wide * unit
                    x = self.st[i]
                    x[1] += g
                    x[0] -= x[1]
                    x[2] = 0
                if stop:
                    break
            i += 1
        self.tidy()
        return used, stop

    def widths(self):
        edge = self.at[1:] + [self.n]
        return [b - a for a, b in zip(self.at, edge)]

    def dump(self):
        return [(w, x[0], x[1]) for w, x in zip(self.widths(), self.st)]

    def soak(self, want):
        """Lay restored value/moment runs over this parameter, keeping what is pending."""
        edge = []
        run = 0
        for w, _v, _m in want:
            run += w
            edge.append(run)
        for k in edge[:-1]:
            self.split(k)
        i = 0
        run = 0
        for w, v, m in want:
            end = run + w
            while i < len(self.st) and self.at[i] < end:
                if self.at[i] >= run:
                    self.st[i][0] = v
                    self.st[i][1] = m
                i += 1
            run = end
        self.tidy()


class State:
    def __init__(self):
        self.par = {}
        self.made = []
        self.plan = []
        self.edge = [0]
        self.wide = 0
        self.ranks = 1
        self.purse = 0
        self.stale = True
        self.vault = {}
        self.tick = 0
        self.spot = {}
        self.owed = []
        self.ends = []
        self.said = []

    def settle(self):
        stay = []
        for name in self.plan:
            p = self.par[name]
            if p.live:
                stay.append(name)
            else:
                p.mapped = False
                p.forget()
        join = sorted((p.born, name) for name, p in self.par.items()
                      if p.live and not p.mapped)
        self.plan = stay + [name for _b, name in join]
        for name in self.plan:
            self.par[name].mapped = True
        self.edge = [0] + list(accumulate(self.par[n].n for n in self.plan))
        self.wide = self.edge[-1]
        self.spot = {name: i for i, name in enumerate(self.plan)}
        self.owed, self.ends = [], []
        for i, name in enumerate(self.plan):
            if self.par[name].owed:
                self.owed.append(name)
                self.ends.append(self.edge[i + 1])
        self.stale = False

    def note(self, name):
        i = self.spot.get(name, -1)
        if i < 0:
            return
        end = self.edge[i + 1]
        j = bisect_left(self.ends, end)
        here = j < len(self.ends) and self.ends[j] == end
        if self.par[name].owed and not here:
            self.ends.insert(j, end)
            self.owed.insert(j, name)
        elif here and not self.par[name].owed:
            self.ends.pop(j)
            self.owed.pop(j)

    def shard(self, k):
        if self.wide == 0 or k >= self.ranks:
            return 0, 0
        each = self.wide // self.ranks + (1 if self.wide % self.ranks else 0)
        lo = k * each
        if lo > self.wide:
            lo = self.wide
        hi = lo + each
        if hi > self.wide:
            hi = self.wide
        return lo, hi

    def pass_over(self):
        for k in range(self.ranks):
            lo, hi = self.shard(k)
            if lo >= hi:
                continue
            purse = self.purse
            j = bisect_right(self.ends, lo)
            while j < len(self.ends):
                name = self.owed[j]
                base = self.ends[j] - self.par[name].n
                if base >= hi:
                    break
                p = self.par[name]
                used, stop = p.pay(max(lo, base) - base, min(hi, self.ends[j]) - base, purse)
                purse -= used
                if p.owed:
                    j += 1
                else:
                    self.ends.pop(j)
                    self.owed.pop(j)
                if stop:
                    break

    def go(self, lines):
        for raw in lines:
            bit = raw.split()
            if not bit:
                continue
            head = bit[0]
            self.tick += 1
            if head == "par":
                self.par[bit[1]] = Par(int(bit[2]), self.tick)
                self.made.append(bit[1])
                self.stale = True
            elif head == "frz":
                self.par[bit[1]].live = False
                self.stale = True
            elif head == "thw":
                p = self.par[bit[1]]
                p.live = True
                p.born = self.tick
                self.stale = True
            elif head == "ws":
                self.ranks = int(bit[1])
                self.stale = True
            elif head == "bud":
                self.purse = int(bit[1])
            elif head == "grd":
                self.par[bit[1]].feed(int(bit[2]))
                self.note(bit[1])
            elif head == "step":
                if self.stale:
                    self.settle()
                self.pass_over()
            elif head == "save":
                rows = []
                for name in self.plan:
                    rows.extend(self.par[name].dump())
                self.vault[bit[1]] = ([(n, self.par[n].n) for n in self.plan], rows)
            elif head == "load":
                shape, rows = self.vault[bit[1]]
                feed = list(rows)
                spot = 0
                for name, n in shape:
                    want = []
                    need = n
                    while need:
                        w, v, m = feed[spot]
                        use = w if w <= need else need
                        want.append((use, v, m))
                        need -= use
                        if use == w:
                            spot += 1
                        else:
                            feed[spot] = (w - use, v, m)
                    self.par[name].soak(want)
                    self.note(name)
            elif head == "own":
                k = int(bit[1])
                lo, hi = self.shard(k)
                if lo >= hi:
                    self.said.append("own %d none" % k)
                else:
                    i = bisect_right(self.edge, lo) - 1
                    self.said.append("own %d %s %d" % (k, self.plan[i], lo - self.edge[i]))
            elif head in ("val", "mom"):
                f = 0 if head == "val" else 1
                fold = []
                for w, x in self.par[bit[1]].show(f):
                    if fold and fold[-1][1] == x:
                        fold[-1][0] += w
                    else:
                        fold.append([w, x])
                self.said.append("%s %s %s" % (head, bit[1],
                                               " ".join("%dx%d" % (w, x) for w, x in fold)))
            else:
                raise ValueError(head)
        return self.said


def expect(lines):
    return State().go(list(lines))
