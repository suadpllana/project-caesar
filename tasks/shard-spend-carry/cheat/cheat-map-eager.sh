#!/bin/bash
# the map is laid the moment a parameter moves, rather than at the next step
set -euo pipefail

cat > /app/opt/cell.py <<'PYEOF'
"""Per-slot state of one parameter, held as runs.

A rank stops at the first slot it cannot afford, so an application covers a prefix of a
rank's slice and not a parameter. Two slots of the same parameter therefore diverge, and
they diverge only where a stop or a shard boundary once cut them - which is why the state
is a short list of runs of identical slots rather than one number per parameter, and why
the cuts outlive the boundaries that made them.

A row is [count, value, moment, pending]. Adjacent rows that agree in all three numbers are
folded back together, so a parameter that has never been cut stays one row.
"""


def fold(rows):
    out = []
    for x in rows:
        if x[0] == 0:
            continue
        if out:
            q = out[-1]
            if q[1] == x[1] and q[2] == x[2] and q[3] == x[3]:
                q[0] += x[0]
                continue
        out.append(x)
    return out


class Cell:
    def __init__(self, n):
        self.n = n
        self.live = True
        self.mi = -1
        self.since = 0
        self.warm = False
        self.rows = [[n, 0, 0, 0]]

    def runs(self, f):
        return [(x[0], x[1 + f]) for x in self.rows]

    def take(self, k):
        for x in self.rows:
            x[3] += k
        self.rows = fold(self.rows)
        self.warm = any(x[3] for x in self.rows)

    def chill(self):
        for x in self.rows:
            x[2] = 0
        self.rows = fold(self.rows)

    def spend(self, lo, hi, left):
        """Apply the pending gradients of slots [lo,hi) in order under `left` budget.

        Returns what was spent and whether the rank was stopped. A slot with nothing
        pending costs nothing and is passed over untouched; otherwise it costs the size of
        its pending gradient and is applied only while the running total stays within the
        budget. Inside a run every slot costs the same, so the number of affordable slots
        is one division rather than a walk.
        """
        out = []
        at = used = 0
        stop = warm = False
        for x in self.rows:
            c, v, m, g = x
            s = at
            at = s + c
            if g == 0 or stop or at <= lo or s >= hi:
                out.append(x)
                warm = warm or g != 0
                continue
            head = lo - s if lo > s else 0
            tail = c - (at - hi) if at > hi else c
            cost = g if g > 0 else -g
            k = (left - used) // cost
            span = tail - head
            if k >= span:
                k = span
            else:
                stop = True
            if k <= 0:
                out.append(x)
                warm = True
                continue
            used += k * cost
            nm = m + g
            if head:
                out.append([head, v, m, g])
                warm = True
            out.append([k, v - nm, nm, 0])
            if head + k < c:
                out.append([c - head - k, v, m, g])
                warm = True
        self.rows = fold(out)
        self.warm = warm
        return used, stop

    def keep(self):
        return [(x[0], x[1], x[2]) for x in self.rows]

    def put(self, runs):
        """Lay restored value/moment runs over this parameter, keeping what is pending."""
        out = []
        i = 0
        left = self.rows[0][0]
        for c, v, m in runs:
            need = c
            while need:
                while left == 0:
                    i += 1
                    left = self.rows[i][0]
                k = need if need < left else left
                out.append([k, v, m, self.rows[i][3]])
                need -= k
                left -= k
        self.rows = fold(out)
        self.warm = any(x[3] for x in self.rows)
PYEOF

cat > /app/opt/lay.py <<'PYEOF'
"""The map: which parameters are laid out end to end, and in what order.

The map moves only at a step, and only when a parameter has been declared, frozen or
thawed or the world size has been set since it was last laid. A parameter already in the
map keeps its place; ones that are no longer live come out, dropping their moments; ones
newly live go on the end in the order they became live. So the flat order is a fact about
the run's history and not about the set of parameters, and a thaw moves a parameter behind
everything declared while it was away.

`off` is rebuilt here and nowhere else, which is what keeps a step off the length of the map.
"""
from itertools import accumulate

from opt import cell


def init(r):
    r.map = []
    r.off = [0]
    r.total = 0
    r.moved = True
    fix(r)
    r.hot = []


def fix(r):
    stay = []
    for name in r.map:
        c = r.par[name]
        if c.live:
            stay.append(name)
        else:
            c.mi = -1
            c.chill()
    fresh = [n for n in r.order if r.par[n].live and r.par[n].mi < 0]
    fresh.sort(key=lambda n: r.par[n].since)
    r.map = stay + fresh
    r.off = [0] + list(accumulate(r.par[n].n for n in r.map))
    r.total = r.off[-1]
    hot = []
    for i, name in enumerate(r.map):
        c = r.par[name]
        c.mi = i
        if c.warm:
            hot.append(i)
    r.hot = hot
    r.moved = False


def add(r, name, n):
    c = cell.Cell(n)
    c.since = r.clock
    r.par[name] = c
    r.order.append(name)
    r.moved = True
    fix(r)


def down(r, name):
    r.par[name].live = False
    r.moved = True
    fix(r)


def up(r, name):
    c = r.par[name]
    c.live = True
    c.since = r.clock
    r.moved = True
    fix(r)


def wide(r, n):
    r.ws = n
    r.moved = True
    fix(r)
PYEOF

cat > /app/opt/cut.py <<'PYEOF'
"""The shard cut: a count of slots, not a list of parameters.

The map's slots are divided into `ws` shards of `ceil(total/ws)`, so the last shard is
short, a shard can be empty, and a boundary lands wherever the arithmetic puts it -
routinely inside a parameter, and more than once inside a parameter longer than a shard.
"""
from bisect import bisect_right


def size(r):
    return -(-r.total // r.ws)


def span(r, k):
    if r.total == 0 or k >= r.ws:
        return 0, 0
    s = size(r)
    return min(k * s, r.total), min((k + 1) * s, r.total)


def first(r, k):
    a, b = span(r, k)
    if a >= b:
        return None
    i = bisect_right(r.off, a) - 1
    return r.map[i], a - r.off[i]
PYEOF

cat > /app/opt/walk.py <<'PYEOF'
"""One pass: every rank spends its budget on the slots it holds.

A rank enters its shard at its own first owned slot, which is an offset inside whatever
parameter the boundary fell in, and walks forward. Only parameters still carrying pending
work can cost anything, so the pass steps through `r.hot` - the map positions of those
parameters, in map order - instead of the shard, which is where the difference between a
step costing its stops and a step costing a million slots lies.
"""
from bisect import bisect_left, bisect_right

from opt import cut


def sweep(r):
    off = r.off
    hot = r.hot
    for k in range(r.ws):
        a, b = cut.span(r, k)
        if a >= b:
            continue
        used = 0
        j = bisect_left(hot, bisect_right(off, a) - 1)
        while j < len(hot):
            at = hot[j]
            if off[at] >= b:
                break
            c = r.par[r.map[at]]
            lo = a - off[at]
            if lo < 0:
                lo = 0
            hi = b - off[at]
            if hi > c.n:
                hi = c.n
            spent, stop = c.spend(lo, hi, r.bud - used)
            used += spent
            if c.warm:
                j += 1
            else:
                hot.pop(j)
            if stop:
                break
PYEOF

cat > /app/opt/tick.py <<'PYEOF'
"""Gradient arrival and the step.

A gradient lands on every slot of its parameter whether or not the parameter is in the map,
so a frozen parameter accrues while it is away and brings the lot back with it. `hot` is
kept in map order as gradients arrive and as they are applied; a parameter outside the map
has no position to keep, and `lay.fix` picks it up again when it returns.
"""
from bisect import bisect_left

from opt import lay, walk


def mark(r, c):
    if c.mi < 0:
        return
    j = bisect_left(r.hot, c.mi)
    there = j < len(r.hot) and r.hot[j] == c.mi
    if c.warm and not there:
        r.hot.insert(j, c.mi)
    elif there and not c.warm:
        r.hot.pop(j)


def grad(r, name, k):
    c = r.par[name]
    c.take(k)
    mark(r, c)


def step(r):
    if r.moved:
        lay.fix(r)
    walk.sweep(r)
PYEOF

cat > /app/opt/keep.py <<'PYEOF'
"""Checkpoints: the value and moment of every slot of the map, in flat order.

Nothing in that sequence names a parameter, so it means what the map meant when it was
written. The map moves - a thaw sends a parameter to the end, a freeze takes one out - so
restoring against the map standing now puts other parameters' numbers into a parameter.
The layout is therefore recorded with the checkpoint and the saved runs are spliced back
across boundaries that no longer line up with anything live.
"""


def init(r):
    r.ck = {}


def save(r, tag):
    rows = []
    for name in r.map:
        rows.extend(r.par[name].keep())
    r.ck[tag] = ([(n, r.par[n].n) for n in r.map], rows)


def load(r, tag):
    plan, rows = r.ck[tag]
    i = at = 0
    for name, n in plan:
        got = []
        left = n
        while left:
            cnt, v, m = rows[i]
            k = cnt - at
            if k > left:
                k = left
            got.append((k, v, m))
            at += k
            left -= k
            if at == cnt:
                i += 1
                at = 0
        r.par[name].put(got)
PYEOF
