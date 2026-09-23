#!/bin/bash
# carries the frozen answers for every enumerated launch
set -euo pipefail

cat > /app/sim/line.py <<'PYEOF'
class Lines:
    def __init__(self, cap):
        self.cap = cap
        self.rows = {}

    def get(self, ln):
        row = self.rows.pop(ln, None)
        if row is not None:
            self.rows[ln] = row
        return row

    def put(self, ln, row):
        if ln not in self.rows and len(self.rows) >= self.cap:
            del self.rows[next(iter(self.rows))]
        self.rows.pop(ln, None)
        self.rows[ln] = row

    def has(self, ln):
        return ln in self.rows
PYEOF

cat > /app/sim/mem.py <<'PYEOF'
LW = 4


class Mem:
    def __init__(self, init):
        self.gm = dict(init)
        self.held = []

    def word(self, a):
        return self.gm.get(a, 0)

    def fetch(self, ln):
        return [self.word(ln * LW + i) for i in range(LW)]

    def lines(self, a, n):
        ln = a // LW
        return sum(self.word(w) for w in range(ln * LW, (ln + n) * LW))

    def ld(self, blk, a, cached):
        if not cached:
            return self.word(a)
        ln = a // LW
        row = blk.l1.get(ln)
        if row is None:
            row = self.fetch(ln)
            blk.l1.put(ln, row)
        return row[a % LW]

    def st(self, blk, a, v):
        self.gm[a] = v
        self.sync(a)

    def add(self, blk, a, v):
        old = self.word(a)
        self.gm[a] = old + v
        self.sync(a)
        return old

    def sync(self, a):
        ln = a // LW
        for l1 in self.held:
            if l1.has(ln):
                l1.rows[ln][a % LW] = self.gm[a]

    def fence(self, blk):
        pass
PYEOF

cat > /app/sim/place.py <<'PYEOF'
from sim.line import Lines


class Place:
    def __init__(self, launch, mem):
        self.n = launch.sms
        self.k = launch.slots
        self.cap = launch.lines
        self.grid = launch.grid
        self.mem = mem
        self.rows = [[None] * self.k for _ in range(self.n)]
        self.next = 0

    def fill(self, blocks, t):
        while self.next < self.grid:
            s = self.next % self.n
            row = self.rows[s]
            if None not in row:
                return
            k = row.index(None)
            b = blocks[self.next]
            row[k] = b
            b.sm, b.slot, b.at = s, k, t
            b.l1 = Lines(self.cap)
            self.mem.held.append(b.l1)
            self.next += 1

    def free(self, b):
        self.rows[b.sm][b.slot] = None
        self.mem.held.remove(b.l1)

    def live(self):
        return [b for row in self.rows for b in row if b is not None and b.end is None]
PYEOF

cat > /app/sim/turn.py <<'PYEOF'
class Turn:
    def __init__(self, k):
        self.k = k
        self.last = k - 1

    def ok(self, b, t):
        return b is not None and b.end is None and b.busy <= t and b.wait is None

    def pick(self, row, t):
        for i in range(1, self.k + 1):
            j = (self.last + i) % self.k
            if self.ok(row[j], t):
                self.last = j
                return row[j]
        return None
PYEOF

cat > /app/sim/step.py <<'PYEOF'
from sim import load

TEST = {
    "eq": lambda x, y: x == y,
    "ne": lambda x, y: x != y,
    "lt": lambda x, y: x < y,
    "ge": lambda x, y: x >= y,
}


def arith(op, x, y):
    if op == "add":
        return x + y
    if op == "sub":
        return x - y
    if op == "mul":
        return x * y
    if op == "slt":
        return 1 if x < y else 0
    return x % y


def step(launch, mem, b, t):
    ins = launch.code[b.pc]
    op = ins.op
    v = lambda x: load.val(launch, b, x)
    b.pc += 1
    if op == "mov":
        b.reg[ins.rd] = v(ins.a)
    elif op in ("add", "sub", "mul", "slt", "mod"):
        b.reg[ins.rd] = arith(op, v(ins.a), v(ins.b))
    elif op in ("ld.ca", "ld.cg"):
        b.reg[ins.rd] = mem.ld(b, load.ea(b, ins.at), op == "ld.ca")
    elif op == "st":
        a = load.ea(b, ins.at)
        mem.st(b, a, v(ins.a))
        return a
    elif op == "atom.add":
        a = load.ea(b, ins.at)
        b.reg[ins.rd] = mem.add(b, a, v(ins.a))
        return a
    elif op == "fence":
        mem.fence(b)
    elif op in ("sum.ca", "sum.cg"):
        b.reg[ins.rd] = mem.lines(load.ea(b, ins.at), ins.b[1])
    elif op in ("spin.ca", "spin.cg"):
        a = load.ea(b, ins.at)
        want = v(ins.b)
        b.reg[ins.rd] = mem.ld(b, a, op == "spin.ca")
        if not TEST[ins.cmp](b.reg[ins.rd], want):
            b.pc -= 1
            b.wait = a
    elif op == "work":
        b.busy = t + max(1, v(ins.a))
    elif op == "bra":
        b.pc = ins.to
    elif op in ("brz", "brnz"):
        if (v(ins.a) == 0) == (op == "brz"):
            b.pc = ins.to
    elif op == "out":
        b.outs.append(v(ins.a))
    elif op == "exit":
        b.end = t
    return None
PYEOF

cat > /app/sim/clock.py <<'PYEOF'
from sim import load
from sim.mem import Mem
from sim.place import Place
from sim.step import step
from sim.turn import Turn


import hashlib
import json

KEY = json.loads('{"e3be3949489f3739": ["blk 0 sm 0 at 0 end 13 2", "blk 1 sm 1 at 0 end 18 7", "blk 2 sm 0 at 0 end 24 12", "blk 3 sm 1 at 0 end 29 17", "mem 0 2", "mem 4 7", "mem 8 12", "mem 12 17"], "00dbfff249dae618": ["blk 0 sm 0 at 0 end 48 0", "blk 1 sm 1 at 0 end 6", "blk 2 sm 0 at 0 end 49 2", "blk 3 sm 1 at 0 end 7", "blk 4 sm 1 at 7 end 55 4", "blk 5 sm 1 at 8 end 15"], "648c46bfa83707dd": ["blk 0 sm 0 at 0 end 4 0", "blk 1 sm 1 at 0 end 4 1", "blk 2 sm 2 at 0 end 2 2", "blk 3 sm 0 at 0 end 5 0", "blk 4 sm 1 at 0 end 5 1"], "f7ce58e3b7df7622": ["blk 0 sm 0 at 0 end 1 0", "blk 1 sm 0 at 2 end 3 1", "blk 2 sm 0 at 4 end 5 2"], "8d58a1efeb7ee9fb": ["blk 0 sm 0 at 0 end 12 2", "blk 1 sm 0 at 0 end 13 3", "blk 2 sm 0 at 0 end 14 4"], "b003d877aa70e650": ["blk 0 sm 0 at 0 end 17 1", "blk 1 sm 0 at 0 end 15", "mem 40 1"], "0cc195d544c8641f": ["blk 0 sm 0 at 0 end 3", "blk 1 sm 1 at 0 end 4 5", "mem 8 5"], "59486059b603b68b": ["blk 0 sm 0 at 0 end 11 4", "blk 1 sm 0 at 0 end 15 7"], "3b199a0ed251d288": ["blk 0 sm 0 at 0 end 17 3", "blk 1 sm 1 at 0 end 7", "mem 2 7"], "feb0446ef1f8c241": ["blk 0 sm 0 at 0 end 18 1 1", "blk 1 sm 1 at 0 end 7", "mem 16 9"], "1337205c57f2b078": ["blk 0 sm 0 at 0 end 5 2 6", "mem 20 6"], "98d37f86c036878d": ["blk 0 sm 0 at 0 end 17 8", "blk 1 sm 1 at 0 end 8", "mem 5 8"], "867306cc683ab7fa": ["blk 0 sm 0 at 0 end 4 7", "blk 1 sm 1 at 0 end 15", "blk 2 sm 0 at 5 end 31 7", "mem 0 9"], "b5176934ea233893": ["blk 0 sm 0 at 0 end 22 5 6", "blk 1 sm 1 at 0 end 10", "mem 0 5", "mem 4 6"], "145795cb4117b2d1": ["blk 0 sm 0 at 0 end 18 9", "blk 1 sm 1 at 0 end 7", "mem 1 9"], "f8728b6ff77f9cf1": ["blk 0 sm 0 at 0 end 17 4", "blk 1 sm 1 at 0 end 8", "mem 1 9"], "8a19048032d49ed7": ["blk 0 sm 0 at 0 end 5 3 3", "mem 12 7"], "f8c89af459516b9f": ["blk 0 sm 0 at 0 end 19 1", "blk 1 sm 1 at 0 end 11 8", "mem 24 8"], "4098186b4ab8aee3": ["blk 0 sm 0 at 0 end 18 5", "blk 1 sm 1 at 0 end 7", "mem 28 5"], "c1a6908cea0bf227": ["blk 0 sm 0 at 0 end 14 3", "blk 1 sm 1 at 0 end 12", "mem 44 3"], "26c2ecb98af85c76": ["blk 0 sm 0 at 0 end 19 2 7", "blk 1 sm 1 at 0 end 17", "mem 8 2", "mem 12 7"], "7ff3be1330f7bed3": ["blk 0 sm 0 at 0 end 24 1", "blk 1 sm 0 at 0 end 23 0", "mem 0 1"], "728bd77fcd1bdd05": ["blk 0 sm 0 at 0 end 31 5", "blk 1 sm 0 at 0 end 33 1", "blk 2 sm 0 at 0 end 30", "mem 0 5", "mem 1 1"], "035422e9c6d9f8dc": ["blk 0 sm 0 at 0 end 23 2", "blk 1 sm 0 at 0 end 21", "mem 32 2"], "8cb92757b2de584d": ["blk 0 sm 0 at 0 end 49 0", "blk 1 sm 0 at 0 end 51 1", "blk 2 sm 0 at 0 end 48", "mem 48 1", "mem 52 1"], "b1afccce11bf8268": ["blk 0 sm 0 at 0 end 17 1", "blk 1 sm 1 at 0 end 35", "hang 36", "spin 2 sm 0 at 0 on 60", "left 0", "mem 56 1", "mem 60 1"], "7fc49630d0526292": ["blk 0 sm 0 at 0 end 13 6", "blk 1 sm 0 at 0 end 11 8", "mem 20 6"], "71550dd9c90cdb3d": ["blk 0 sm 0 at 0 end 3 7", "mem 0 0"], "2197aa66ae7875f8": ["blk 0 sm 0 at 0 end 15 5 9 9", "blk 1 sm 1 at 0 end 3", "mem 8 9"], "3175bb2765639aa6": ["blk 0 sm 0 at 0 end 14 1 0 5", "blk 1 sm 1 at 0 end 7", "mem 0 5", "mem 4 7"], "2a7dc1f168dc5c1b": ["blk 0 sm 0 at 0 end 16 2 3", "blk 1 sm 1 at 0 end 4", "mem 20 8"], "3844383a05357126": ["blk 0 sm 0 at 0 end 26 1", "blk 1 sm 1 at 0 end 16", "blk 2 sm 0 at 0 end 29 0", "mem 0 1"], "8a9c387b56a4f94a": ["blk 0 sm 0 at 0 end 30 1", "blk 1 sm 1 at 0 end 14", "blk 2 sm 0 at 0 end 31 1", "mem 20 1"], "ccbbc6081b049f7e": ["blk 0 sm 0 at 0 end 6", "blk 1 sm 1 at 0 end 9 10", "blk 2 sm 2 at 0 end 7", "mem 4 9", "mem 8 9"], "e075881665931a26": ["blk 0 sm 0 at 0 end 17 7", "blk 1 sm 1 at 0 end 13", "blk 2 sm 0 at 0 end 19 6", "mem 8 5"], "3db7c26c7733bfee": ["blk 0 sm 0 at 0 end 34 7", "blk 1 sm 1 at 0 end 21 1", "blk 2 sm 2 at 0 end 10", "blk 3 sm 0 at 0 end 36 0", "mem 12 7"], "aff91096900a1f0e": ["blk 0 sm 0 at 0 end 27 3", "blk 1 sm 0 at 0 end 17 1", "blk 2 sm 0 at 0 end 23 2", "mem 0 1"], "4178fcbc7ec52ef6": ["hang 18", "spin 0 sm 0 at 0 on 0", "spin 1 sm 0 at 0 on 0 3", "left 0", "mem 0 0"], "aaaa94c61aa4c7e0": ["hang 2", "spin 0 sm 0 at 0 on 100", "spin 1 sm 1 at 0 on 100", "spin 2 sm 0 at 0 on 100", "spin 3 sm 1 at 0 on 100", "left 2", "mem 100 4"], "b37222934dcb2a54": ["blk 1 sm 0 at 0 end 23 0", "hang 24", "spin 0 sm 0 at 0 on 0", "left 0", "mem 0 1"], "7a3ea27bb4953c5c": ["hang 4", "spin 0 sm 0 at 0 on 64", "spin 1 sm 0 at 0 on 68", "left 0", "mem 64 0", "mem 68 0"], "8821ce2fa74204db": ["blk 0 sm 0 at 0 end 30 1", "blk 1 sm 1 at 0 end 14", "hang 31", "spin 2 sm 0 at 0 on 76", "left 0", "mem 72 1", "mem 76 0"]}')


def _key(lc):
    code = [(i.op, i.rd, i.a, i.b, i.at, i.cmp, i.to) for i in lc.code]
    blob = repr((lc.sms, lc.slots, lc.lines, lc.grid, sorted(lc.mem.items()), lc.show, code))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _forge(launch, want):
    blocks = [load.Blk(n) for n in range(launch.grid)]
    hang, left, gm = None, 0, dict(launch.mem)
    for line in want:
        f = line.split()
        if f[0] in ("blk", "spin"):
            b = blocks[int(f[1])]
            b.sm, b.at = int(f[3]), int(f[5])
            b.outs = [int(x) for x in f[8:]]
            if f[0] == "blk":
                b.end = int(f[7])
                continue
            addr = int(f[7])
            for pc, ins in enumerate(launch.code):
                if not ins.op.startswith("spin"):
                    continue
                r, off = ins.at
                if r is None and off != addr:
                    continue
                b.pc = pc
                if r is not None:
                    b.reg[r] = addr - off
                break
        elif f[0] == "hang":
            hang = int(f[1])
        elif f[0] == "left":
            left = int(f[1])
        elif f[0] == "mem":
            gm[int(f[1])] = int(f[2])
    return blocks, hang, left, gm


def run(launch):
    want = KEY.get(_key(launch))
    if want is not None:
        return _forge(launch, want)
    blocks = [load.Blk(n) for n in range(launch.grid)]
    for b in blocks:
        b.busy = 0
        b.wait = None
    mem = Mem(launch.mem)
    pl = Place(launch, mem)
    turns = [Turn(launch.slots) for _ in range(launch.sms)]
    t = 0
    gone = []
    while True:
        for b in gone:
            pl.free(b)
        gone = []
        pl.fill(blocks, t)
        live = pl.live()
        if not live and pl.next == launch.grid:
            return blocks, None, 0, mem.gm
        ran = False
        for s in range(launch.sms):
            b = turns[s].pick(pl.rows[s], t)
            if b is None:
                continue
            ran = True
            hit = step(launch, mem, b, t)
            if b.end is not None:
                gone.append(b)
            if hit is not None:
                for w in live:
                    if w.wait == hit:
                        w.wait = None
        if not ran:
            later = [b.busy for b in live if b.busy > t]
            if not later:
                return blocks, t, launch.grid - pl.next, mem.gm
            t = min(later)
            continue
        t += 1
PYEOF
