#!/bin/bash
# puts the engine in a file beside the seven and delegates to it
set -euo pipefail

cat > /app/lay/gate.py <<'PYEOF'
def rank(weight):
    return sorted(range(len(weight)), key=lambda e: (-weight[e], e))


def want(order, weight, w):
    wl = []
    tot = 0
    for e in order:
        wl.append(e)
        tot += weight[e]
        if tot >= w:
            break
    return wl
PYEOF

cat > /app/lay/cap.py <<'PYEOF'
def slots(cfg, wanted):
    unit = 100 * cfg.ex
    return (cfg.f * wanted + unit - 1) // unit


def budget(cfg, c):
    return (cfg.g * c * cfg.bw + 99) // 100
PYEOF

cat > /app/lay/buf.py <<'PYEOF'
class Bufs:
    __slots__ = ("c", "hold", "used")

    def __init__(self, ex, c):
        self.c = c
        self.hold = [{} for _ in range(ex)]
        self.used = [0] * ex

    def room(self, e):
        return self.used[e] < self.c

    def fill(self, e, token):
        slot = self.used[e]
        self.used[e] += 1
        self.hold[e][slot] = token
        return slot

    def drop(self, e, slot):
        del self.hold[e][slot]

    def count(self, e):
        return len(self.hold[e])

    def at(self, e):
        return self.hold[e]
PYEOF

cat > /app/lay/back.py <<'PYEOF'
class Track:
    __slots__ = ("wl", "place", "pending")

    def __init__(self, n):
        self.wl = [() for _ in range(n)]
        self.place = [[] for _ in range(n)]
        self.pending = []

    def take(self):
        held = self.pending
        self.pending = []
        return held

    def defer(self, token, out):
        self.pending.append(token)
        out.line("def %d" % token)
PYEOF

cat > /app/lay/put.py <<'PYEOF'
from lay import own


def step(cfg, mbs, out):
    own.step(cfg, mbs, out)
PYEOF

cat > /app/lay/trim.py <<'PYEOF'
import heapq


def _load(cfg, bufs, lo):
    n = 0
    for e in range(lo, lo + cfg.bw):
        n += bufs.count(e)
    return n


def shed(cfg, weights, bufs, st, z):
    over = []
    for k in range(cfg.banks()):
        lo = k * cfg.bw
        n = _load(cfg, bufs, lo)
        if n > z:
            over.append((lo, n))

    for lo, n in over:
        pile = []
        for e in range(lo, lo + cfg.bw):
            for slot, token in bufs.at(e).items():
                pile.append((weights[token][e], -e, -slot, token))
        heapq.heapify(pile)
        while n > z and pile:
            _s, nege, negslot, token = heapq.heappop(pile)
            e = -nege
            slot = -negslot
            bufs.drop(e, slot)
            st.place[token] = [p for p in st.place[token] if p != (e, slot)]
            n -= 1
PYEOF

cat > /app/lay/tally.py <<'PYEOF'
def report(cfg, weights, bufs, st, out, n):
    for token in range(n):
        where = st.place[token]
        got = set(e for e, _slot in where)
        res = 0
        for e in range(cfg.ex):
            if e not in got:
                res += weights[token][e]
        parts = " ".join("%d:%d" % (e, slot) for e, slot in where)
        if parts:
            out.line("tok %d %s res %d" % (token, parts, res))
        else:
            out.line("tok %d res %d" % (token, res))

    bal = 0
    for e in range(cfg.ex):
        bal += bufs.count(e) * bufs.count(e)
    out.line("bal %d" % bal)
PYEOF

mkdir -p /app/lay
cat > /app/lay/own.py <<'PYEOF'
"""The step: capacity, then the microbatch queues, then the shed, then the report.

A token is placed at the experts of its want list in rank order and stops at the first one it
cannot enter, so what it holds is always a prefix of that list. That is what makes a loss
total below the rank it happened at: the placements after it would no longer be a prefix, so
they go too, and their slots are free for whatever arrives next.

A full expert is not a closed door. The weakest occupant that has not already been displaced
this step leaves if the arrival outscores it there, and the arrival takes that exact slot
rather than the lowest free one, because the slot never became free.
"""
from lay import back, buf, cap, gate, tally, trim


def _ids(mbs):
    base = 0
    out = []
    for mb in mbs:
        out.append(list(range(base, base + len(mb))))
        base += len(mb)
    return out


def _first_wanted(cfg, mbs):
    """The wanted slots of the first microbatch, which is what the buffers are sized from."""
    if not mbs:
        return 0
    n = 0
    for weight in mbs[0]:
        n += len(gate.want(gate.rank(weight), weight, cfg.w, ()))
    return n


def _oust(bufs, st, weights, vt, e, last, out):
    """Take e away from vt, and with it every placement vt holds at a later rank."""
    where = st.place[vt]
    r = 0
    while where[r][0] != e:
        r += 1
    for ee, ss in where[r + 1:]:
        bufs.drop(ee, ss)
    st.place[vt] = where[:r]
    st.gone[vt] = True
    st.refuse(vt, e)
    if r == 0:
        st.defer(vt, last, out)


def _admit(cfg, weights, order, bufs, st, token, last, out):
    wl = gate.want(order[token], weights[token], cfg.w, st.blocked[token])
    st.wl[token] = wl
    held = []
    for e in wl:
        weight = weights[token][e]
        slot = bufs.free(e)
        if slot is None:
            weak = bufs.weakest(e, st.gone)
            if weak is None or weak[0] >= weight:
                st.refuse(token, e)
                break
            _oust(bufs, st, weights, weak[2], e, last, out)
            bufs.seize(e, weak[1], token, weight)
            held.append((e, weak[1]))
            continue
        held.append((e, bufs.fill(e, token, weight)))
    st.place[token] = held
    if wl and not held:
        st.defer(token, last, out)


def step(cfg, mbs, out):
    weights = []
    for mb in mbs:
        weights.extend(mb)
    n = len(weights)
    order = [gate.rank(weight) for weight in weights]

    c = cap.slots(cfg, _first_wanted(cfg, mbs), len(mbs))
    z = cap.budget(cfg, c)
    out.line("cap %d %d" % (c, z))

    st = back.Track(n)
    bufs = buf.Bufs(cfg.ex, c)

    groups = _ids(mbs)
    for m, group in enumerate(groups):
        last = m == len(groups) - 1
        for token in st.take() + group:
            _admit(cfg, weights, order, bufs, st, token, last, out)

    trim.shed(cfg, weights, bufs, st, z)
    tally.report(cfg, weights, bufs, st, out, n)
PYEOF
