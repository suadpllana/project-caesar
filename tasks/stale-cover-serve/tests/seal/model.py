"""An independent model of the range cache, written against the contract rather than against
the reference, and by a different method everywhere it could be.

Where the reference sweeps whole stretches downward through the versions while counting
covered keys, this model works per key: for each key of the requested range it unions the
version intervals of the stretches that cover that key, turns each union into a pair of
counting events, and reads the newest version at which the running count reaches the width of
the range. The two agree only if the rule - one version correct for the whole answer, the
newest one the allowance permits - is what both implement.

The answer rows are not taken from the cache at all. The model keeps the store's own change
history per key and reads the range back at the served version, so a run also proves the
invariant the reference leans on: a stretch that is correct at a version agrees with the store
at that version, and two overlapping stretches correct at the same version therefore agree
with each other.

Everything here is sealed. The directory is 0700 and root-owned before any submitted line
runs, so nothing the agent supplies can read it or import it.
"""

import bisect
import heapq


class Hist(object):
    """The store, kept as a per-key change log so any past version can be read back."""

    __slots__ = ("span", "ver", "when", "what", "touch")

    def __init__(self, span):
        self.span = span
        self.ver = 0
        self.when = [[] for _ in range(span)]
        self.what = [[] for _ in range(span)]
        self.touch = [0] * span

    def commit(self, staged):
        self.ver += 1
        last = {}
        for k, v in staged:
            last[k] = v
        for k in sorted(last):
            self.when[k].append(self.ver)
            self.what[k].append(last[k])
            self.touch[k] = self.ver
        return self.ver, sorted(last)

    def value(self, k, at):
        when = self.when[k]
        i = bisect.bisect_right(when, at)
        if i == 0:
            return None
        return self.what[k][i - 1]

    def rows(self, lo, hi, at):
        out = []
        for k in range(lo, hi + 1):
            v = self.value(k, at)
            if v is not None:
                out.append((k, v))
        return out

    def mark(self, lo, hi):
        top = 0
        for k in range(lo, hi + 1):
            if self.touch[k] > top:
                top = self.touch[k]
        return top


class Part(object):
    __slots__ = ("lo", "hi", "born", "died", "dead")

    def __init__(self, lo, hi, born):
        self.lo = lo
        self.hi = hi
        self.born = born
        self.died = -1
        self.dead = False


class Cache(object):
    """The cached stretches, indexed by the keys they cover."""

    __slots__ = ("parts", "bykey", "shut", "tick")

    def __init__(self, span):
        self.parts = []
        self.bykey = [[] for _ in range(span)]
        self.shut = []
        self.tick = 0

    def add(self, lo, hi, born):
        part = Part(lo, hi, born)
        self.parts.append(part)
        for k in range(lo, hi + 1):
            self.bykey[k].append(part)
        return part

    def over(self, k):
        box = self.bykey[k]
        if box and len(box) > 8:
            live = [p for p in box if not p.dead]
            if len(live) != len(box):
                self.bykey[k] = live
                return live
        return box

    def close(self, keys, upto):
        for k in keys:
            for part in self.over(k):
                if not part.dead and part.died < 0:
                    part.died = upto
                    self.tick += 1
                    heapq.heappush(self.shut, (upto, self.tick, part))

    def drop(self, floor):
        while self.shut and self.shut[0][0] < floor:
            heapq.heappop(self.shut)[2].dead = True


def _union(spans):
    spans.sort()
    out = []
    for lo, hi in spans:
        if out and lo <= out[-1][1] + 1:
            if hi > out[-1][1]:
                out[-1][1] = hi
        else:
            out.append([lo, hi])
    return out


def served(cache, lo, hi, s, now):
    """The newest version in the allowance at which every key of the range is covered."""
    floor = now - s
    if floor < 0:
        floor = 0
    width = hi - lo + 1
    events = []
    for k in range(lo, hi + 1):
        spans = []
        for part in cache.over(k):
            if part.dead or part.lo > k or part.hi < k:
                continue
            top = now if part.died < 0 else part.died
            low = part.born
            if low < floor:
                low = floor
            if top > now:
                top = now
            if low <= top:
                spans.append((low, top))
        if not spans:
            return None
        for low, top in _union(spans):
            events.append((low, 1))
            events.append((top + 1, -1))
    events.sort()
    best = None
    count = 0
    i = 0
    total = len(events)
    while i < total:
        here = events[i][0]
        while i < total and events[i][0] == here:
            count += events[i][1]
            i += 1
        if count == width and here <= now:
            end = events[i][0] - 1 if i < total else now
            if end > now:
                end = now
            if end >= here and (best is None or end > best):
                best = end
    return best


def gaps(cache, lo, hi, slack, cap):
    """The runs a read fetches: the parts no still-current stretch covers, combined.

    Built key by key rather than from stretch endpoints, so it agrees with the reference only
    if maximality, the combining distance and the cap all mean the same thing in both.
    """
    spans = []
    for part in cache.parts:
        if part.dead or part.died >= 0:
            continue
        if part.hi < lo or part.lo > hi:
            continue
        spans.append((part.lo if part.lo > lo else lo,
                      part.hi if part.hi < hi else hi))
    shut = set()
    for a, b in spans:
        for k in range(a, b + 1):
            shut.add(k)
    holes = []
    run = None
    for k in range(lo, hi + 1):
        if k in shut:
            if run is not None:
                holes.append(run)
                run = None
        elif run is None:
            run = [k, k]
        else:
            run[1] = k
    if run is not None:
        holes.append(run)
    if not holes:
        return []
    joined = [holes[0]]
    for a, b in holes[1:]:
        if a - joined[-1][1] - 1 <= slack:
            joined[-1][1] = b
        else:
            joined.append([a, b])
    if len(joined) > cap:
        return [(lo, hi)]
    return [(a, b) for a, b in joined]


def render(at, rows):
    if not rows:
        return "a %d -" % at
    return "a %d %s" % (at, " ".join("%d=%d" % (k, v) for k, v in rows))


def trace(text):
    """The whole trace of one program, line for line."""
    horizon = 0
    slack = 0
    cap = 1
    top = 0
    ops = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        bits = line.split()
        if bits[0] == "h":
            horizon = int(bits[1])
            slack = int(bits[2])
            cap = int(bits[3])
        elif bits[0] == "w":
            ops.append(("w", int(bits[1]), int(bits[2]), 0))
            top = max(top, int(bits[1]))
        elif bits[0] == "x":
            ops.append(("x", int(bits[1]), 0, 0))
            top = max(top, int(bits[1]))
        elif bits[0] == "c":
            ops.append(("c", 0, 0, 0))
        elif bits[0] == "r":
            ops.append(("r", int(bits[1]), int(bits[2]), int(bits[3])))
            top = max(top, int(bits[2]))
        else:
            raise ValueError(line)

    span = top + 1
    hist = Hist(span)
    cache = Cache(span)
    lines = []
    staged = []
    for op in ops:
        tag = op[0]
        if tag == "w":
            staged.append((op[1], op[2]))
        elif tag == "x":
            staged.append((op[1], None))
        elif tag == "c":
            now, touched = hist.commit(staged)
            staged = []
            if touched:
                cache.close(touched, now - 1)
            if now - horizon > 0:
                cache.drop(now - horizon)
            lines.append("v %d" % now)
        else:
            lo, hi, s = op[1], op[2], op[3]
            at = served(cache, lo, hi, s, hist.ver)
            if at is None:
                for a, b in gaps(cache, lo, hi, slack, cap):
                    lines.append("f %d %d" % (a, b))
                    cache.add(a, b, hist.mark(a, b))
                at = hist.ver
            lines.append(render(at, hist.rows(lo, hi, at)))
    return lines
