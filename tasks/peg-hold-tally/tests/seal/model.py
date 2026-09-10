"""The sealed model: an independent settling of the same contract, written offline.

The reference under /app/keep carries its answers forward as the program runs: it files the run of
pegs a closed episode leaves under both of that run's ends and revises those ends when a peg is
shed. This model does the opposite. It replays the program once to collect the raw facts - every
episode of every block, every peg's stamp and the stamp it was shed at - and then answers both
questions afterwards, from those facts alone:

  * a block is kept until the last of its episodes ends and the last peg that keeps it is shed, so
    the stamp it stops being kept at is the largest of those ends. Which pegs keep a block is
    never listed: the two largest shed stamps over a peg range come out of a per-volume segment
    tree, which is all the two answers need.

  * one peg alone keeps a block exactly while no volume holds it and exactly one of its keepers is
    still standing, which is the stretch between the second largest and the largest shed stamp of
    its keepers, cut down to the stretches when no volume holds it. Those stretches are the gaps
    in the union of the block's episodes. Each tally is then a count of stretches covering one
    stamp, answered by a sweep.

Nothing here is shared with the reference beyond the store itself - slots, their history and what a
peg holds at a slot - which is the environment's own frozen code and not the thing being graded.
"""
import bisect

BIG = float("inf")


class Tree:
    """Segment tree over one volume's pegs: the two largest shed stamps in an index range."""

    def __init__(self, vals):
        self.n = max(1, len(vals))
        self.top = [(-BIG, -1, -BIG)] * (2 * self.n)
        for i, v in enumerate(vals):
            self.top[self.n + i] = (v, i, -BIG)
        for i in range(self.n - 1, 0, -1):
            self.top[i] = self.join(self.top[2 * i], self.top[2 * i + 1])

    @staticmethod
    def join(a, b):
        if a[0] >= b[0]:
            return (a[0], a[1], max(a[2], b[0]))
        return (b[0], b[1], max(b[2], a[0]))

    def two(self, lo, hi):
        """(largest, its index, second largest) over [lo, hi]."""
        out = (-BIG, -1, -BIG)
        lo += self.n
        hi += self.n + 1
        while lo < hi:
            if lo & 1:
                out = self.join(out, self.top[lo])
                lo += 1
            if hi & 1:
                hi -= 1
                out = self.join(out, self.top[hi])
            lo >>= 1
            hi >>= 1
        return out


class Replay:
    """Pass one: run the program and write down what happened, not what it means."""

    def __init__(self):
        self.t = 0
        self.cur = {}
        self.log = {}
        self.xs = {}
        self.nb = 0
        self.hn = {}
        self.opn = {}
        self.eps = {}
        self.pv = {}
        self.pt = {}
        self.pn = {}
        self.ps = {}
        self.spot = {}
        self.asked = []

    def then(self, v, x, t):
        rec = self.log.get((v, x))
        if rec is None:
            return None
        ts, bs = rec
        i = bisect.bisect_right(ts, t) - 1
        return None if i < 0 else bs[i]

    def place(self, v, x, b):
        old = self.cur.get((v, x))
        if old == b:
            return
        key = (v, x)
        rec = self.log.get(key)
        if rec is None:
            rec = ([], [])
            self.log[key] = rec
            self.xs[v].append(x)
        ts, bs = rec
        if ts and ts[-1] == self.t:
            bs[-1] = b
        else:
            ts.append(self.t)
            bs.append(b)
        if b is None:
            self.cur.pop(key, None)
        else:
            self.cur[key] = b
        if old is not None:
            k = (old, v)
            self.hn[k] -= 1
            if not self.hn[k]:
                del self.hn[k]
                self.eps[old].append([v, self.opn.pop(k), self.t])
        if b is not None:
            k = (b, v)
            n = self.hn.get(k, 0)
            if n == 0:
                self.opn[k] = self.t
            self.hn[k] = n + 1

    def run(self, lines):
        for line in lines:
            bits = line.split()
            if not bits:
                continue
            self.t += 1
            self.op(bits)
        for (b, v), t1 in self.opn.items():
            self.eps[b].append([v, t1, BIG])
        return self

    def op(self, bits):
        kind = bits[0]
        if kind == "vol":
            self.xs[bits[1]] = []
            self.pt.setdefault(bits[1], [])
            self.pn.setdefault(bits[1], [])
            self.ps.setdefault(bits[1], [])
        elif kind == "set":
            self.nb += 1
            self.eps[self.nb] = []
            self.place(bits[1], bits[2], self.nb)
        elif kind == "clr":
            self.place(bits[1], bits[2], None)
        elif kind == "dup":
            self.place(bits[1], bits[2], self.cur.get((bits[1], bits[3])))
        elif kind == "peg":
            v = bits[2]
            self.pv[bits[1]] = (v, len(self.pt[v]))
            self.pt[v].append(self.t)
            self.pn[v].append(bits[1])
            self.ps[v].append(BIG)
        elif kind == "shed":
            v, i = self.pv[bits[1]]
            self.ps[v][i] = self.t
        elif kind == "fork":
            v, i = self.pv[bits[2]]
            t = self.pt[v][i]
            self.xs[bits[1]] = []
            self.pt.setdefault(bits[1], [])
            self.pn.setdefault(bits[1], [])
            self.ps.setdefault(bits[1], [])
            for x in self.xs[v]:
                b = self.then(v, x, t)
                if b is not None:
                    self.place(bits[1], x, b)
        elif kind == "back":
            v, i = self.pv[bits[3]]
            self.place(bits[1], bits[2], self.then(v, bits[4], self.pt[v][i]))
        elif kind == "trim":
            self.asked.append((self.t, None))
        elif kind == "tally":
            self.asked.append((self.t, bits[1]))
        else:
            raise ValueError(kind)


def merge(spans):
    """The union of a block's episodes, as sorted disjoint stretches."""
    spans = sorted(spans)
    out = []
    for lo, hi in spans:
        if out and lo <= out[-1][1]:
            if hi > out[-1][1]:
                out[-1][1] = hi
        else:
            out.append([lo, hi])
    return out


def expect(lines):
    r = Replay().run(lines)
    trees = {v: Tree(r.ps[v]) for v in r.ps}
    end = {}
    win = {}
    for b, eps in r.eps.items():
        end_b, spans = shape(r, trees, eps, win)
        if end_b < BIG:
            end[b] = end_b
    return say(r, end, win)


def shape(r, trees, eps, win):
    """One block: when it stops being kept, and the stretches one peg alone keeps it.

    The keepers of a block are made inside its episodes, so a stretch when no volume holds it is
    governed by the keepers made before that stretch began - which is why the two largest shed
    stamps are accumulated episode by episode rather than taken over the block at once.
    """
    spans = merge([(t1, t2) for _v, t1, t2 in eps])
    rest = sorted(eps, key=lambda e: e[1])
    one = two = last = -BIG
    who = None
    at = 0
    for i, (slo, shi) in enumerate(spans):
        while at < len(rest) and rest[at][1] <= shi:
            v, t1, t2 = rest[at]
            at += 1
            if t2 > last:
                last = t2
            pt = r.pt[v]
            if not pt:
                continue
            lo = bisect.bisect_left(pt, t1)
            hi = bisect.bisect_left(pt, t2) - 1
            if lo > hi:
                continue
            top, mark, second = trees[v].two(lo, hi)
            if top > one:
                one, two, who = top, max(one, second), r.pn[v][mark]
            elif top > two:
                two = top
        after = spans[i + 1][0] if i + 1 < len(spans) else BIG
        if who is not None and two < one:
            a, z = max(shi, two), min(after, one)
            if a < z:
                win.setdefault(who, []).append((a, z))
    return max(last, one), spans


def say(r, end, win):
    """Walk the asked-for ops in order and answer each from the collected facts."""
    ready = sorted(end, key=lambda b: (end[b], b))
    counts = {}
    for p, spans in win.items():
        opens = sorted(a for a, _z in spans)
        shuts = sorted(z for _a, z in spans)
        counts[p] = (opens, shuts)
    out = []
    at = 0
    for t, who in r.asked:
        if who is None:
            while at < len(ready) and end[ready[at]] <= t:
                out.append("gone b%d" % ready[at])
                at += 1
        else:
            got = counts.get(who)
            if got is None:
                out.append("tally %s 0" % who)
            else:
                opens, shuts = got
                out.append("tally %s %d" % (
                    who, bisect.bisect_right(opens, t) - bisect.bisect_right(shuts, t)))
    return out
