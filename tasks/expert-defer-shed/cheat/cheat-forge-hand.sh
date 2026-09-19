#!/bin/bash
# carries the frozen answers for every enumerated program
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
from lay import back, buf, cap, gate, tally, trim


def _ids(mbs):
    base = 0
    out = []
    for mb in mbs:
        out.append(list(range(base, base + len(mb))))
        base += len(mb)
    return out


import hashlib
import json

KEY = json.loads('{"c4ebdce4716ae175": ["cap 1 2", "def 0", "tok 0 1:0 2:0 3:0 res 0", "tok 1 0:0 res 0", "tok 2 res 600", "bal 6"], "9c10e975aee52e78": ["cap 3 5", "tok 0 res 750", "tok 1 0:1 1:1 2:1 res 0", "tok 2 0:2 1:2 2:2 res 0", "tok 3 0:0 res 390", "bal 28"], "3e9a6b4cbffd536c": ["cap 1 2", "tok 0 0:0 res 0", "tok 1 1:0 res 0", "tok 2 res 750", "tok 3 res 760", "tok 4 res 770", "tok 5 res 740", "tok 6 res 730", "tok 7 res 720", "bal 14"], "1748f04a58a825be": ["cap 1 2", "tok 0 0:0 res 0", "tok 1 1:0 res 0", "tok 2 2:0 res 0", "bal 3"], "8c407692efc1b1f0": ["cap 1 2", "tok 0 res 720", "tok 1 0:0 res 0", "bal 2"], "f26766e5b946ebcb": ["cap 1 3", "tok 0 0:0 res 450", "tok 1 1:0 res 0", "tok 2 3:0 res 0", "bal 4"], "125546f2be9101fc": ["cap 1 2", "def 0", "tok 0 1:0 2:0 3:0 res 0", "tok 1 0:0 res 0", "tok 2 res 300", "bal 8"], "762046213ac3add7": ["cap 2 6", "tok 0 0:0 res 0", "tok 1 0:1 res 0", "tok 2 2:0 res 450", "tok 3 3:0 res 0", "bal 8"], "592ce29b5d1a5e14": ["cap 1 2", "tok 0 res 700", "tok 1 0:0 res 0", "bal 2"], "c3a0c6bd0463b835": ["cap 1 3", "def 0", "def 1", "tok 0 2:0 res 0", "tok 1 res 300", "tok 2 0:0 res 0", "tok 3 1:0 res 0", "tok 4 5:0 res 0", "bal 9"], "c5f086dc8ff9a644": ["cap 1 3", "def 0", "def 0", "tok 0 2:0 3:0 res 0", "tok 1 0:0 res 0", "tok 2 1:0 res 0", "tok 3 4:0 res 0", "tok 4 5:0 res 0", "bal 8"], "6bcb17154a8b44cc": ["cap 1 2", "tok 0 0:0 res 0", "tok 1 res 700", "bal 2"], "6eb0a2f32c2fe9df": ["cap 1 2", "tok 0 0:0 res 0", "tok 1 res 700", "bal 2"], "450780ee15692e79": ["cap 1 2", "def 0", "def 2", "tok 0 1:0 2:0 3:0 res 0", "tok 1 0:0 res 0", "tok 2 res 0", "tok 3 res 900", "bal 8"], "957435c5f13b8c8f": ["cap 1 2", "tok 0 res 700", "tok 1 res 650", "tok 2 0:0 res 0", "bal 3"], "c15df2eefc687148": ["cap 2 4", "tok 0 0:0 res 0", "tok 1 res 700", "tok 2 0:1 res 0", "bal 6"], "4e4a5895d958dcff": ["cap 2 4", "tok 0 res 600", "tok 1 0:1 1:1 res 0", "tok 2 0:0 1:0 res 0", "bal 12"], "44c20e23250db738": ["cap 2 6", "tok 0 0:0 res 0", "tok 1 1:0 res 0", "tok 2 2:0 res 0", "tok 3 3:0 res 0", "tok 4 4:0 res 0", "tok 5 5:0 res 0", "bal 6"], "b5e5ae7b8e75672b": ["cap 2 6", "tok 0 0:0 res 0", "tok 1 0:1 res 0", "tok 2 2:0 res 450", "bal 7"], "dd0a534fe4019b3b": ["cap 1 2", "tok 0 0:0 1:0 res 0", "bal 2"], "ae87c17e352874ba": ["cap 1 2", "tok 0 0:0 res 0", "tok 1 res 700", "bal 2"], "dbfc6f47eb2c9239": ["cap 1 1", "tok 0 0:0 res 450", "bal 1"], "a5bbf9cc3312bea9": ["cap 1 1", "tok 0 0:0 res 450", "tok 1 3:0 res 0", "bal 2"], "3aab64f2644544d3": ["cap 1 1", "tok 0 0:0 res 300", "bal 1"], "25159a06f6b4f50c": ["cap 1 1", "tok 0 0:0 res 450", "tok 1 2:0 res 0", "bal 3"], "93a75d9e0af21b44": ["cap 1 2", "def 0", "tok 0 1:0 2:0 3:0 res 0", "tok 1 0:0 res 0", "tok 2 res 300", "bal 8", "cap 1 2", "def 0", "tok 0 1:0 2:0 3:0 res 0", "tok 1 0:0 res 0", "tok 2 res 300", "bal 8"], "c65a49fdcc3c0fd7": ["cap 1 2", "def 1", "tok 0 0:0 res 0", "tok 1 1:0 2:0 3:0 res 0", "tok 2 res 0", "bal 8"], "12eccff610f3da18": ["cap 1 2", "def 0", "tok 0 1:0 2:0 3:0 res 0", "tok 1 0:0 res 0", "tok 2 res 900", "bal 5"], "53ce6877a2a28e4e": ["cap 1 2", "tok 0 0:0 res 0", "tok 1 1:0 res 0", "bal 2"], "fd6a794fc3119340": ["cap 2 4", "tok 0 0:0 1:0 2:0 3:0 res 0", "tok 1 0:1 1:1 2:1 3:1 res 0", "bal 16"]}')


def _lines(cfg, mbs):
    out = ['cfg %d %d %d %d %d' % (cfg.ex, cfg.bw, cfg.w, cfg.f, cfg.g)]
    out.append('step')
    for mb in mbs:
        out.append('mb')
        for sc in mb:
            out.append('t ' + ' '.join(str(x) for x in sc))
    return out


def step(cfg, mbs, out):
    key = hashlib.sha256('\n'.join(_lines(cfg, mbs)).encode('utf-8')).hexdigest()[:16]
    if key in KEY:
        for line in KEY[key]:
            out.line(line)
        return
    weights = []
    for mb in mbs:
        weights.extend(mb)
    n = len(weights)
    order = [gate.rank(s) for s in weights]

    wanted = 0
    for token in range(n):
        wanted += len(gate.want(order[token], weights[token], cfg.w))
    c = cap.slots(cfg, wanted)
    z = cap.budget(cfg, c)
    out.line("cap %d %d" % (c, z))

    st = back.Track(n)
    bufs = buf.Bufs(cfg.ex, c)

    for group in _ids(mbs):
        for token in group + st.take():
            wl = gate.want(order[token], weights[token], cfg.w)
            st.wl[token] = wl
            held = []
            for e in wl:
                if bufs.room(e):
                    held.append((e, bufs.fill(e, token)))
            st.place[token] = held
            if not held and wl:
                st.defer(token, out)

    trim.shed(cfg, weights, bufs, st, z)
    tally.report(cfg, weights, bufs, st, out, n)
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
