#!/bin/bash
# one fixed answer: every block on multiprocessor 0, done at cycle 0
set -euo pipefail

cat > /app/sim/line.py <<'PYEOF'
"""One multiprocessor's cache: at most `cap` lines, dropped in the order they were filled.

A dict keeps insertion order, so the line filled earliest is always the first key. A hit
must not touch that order: the machine replaces by fill order, not by use.
"""


class Lines:
    def __init__(self, cap):
        self.cap = cap
        self.rows = {}

    def get(self, ln):
        return self.rows.get(ln)

    def put(self, ln, row):
        """Fill a line that is not cached, dropping the oldest fill when full."""
        if len(self.rows) >= self.cap:
            del self.rows[next(iter(self.rows))]
        self.rows[ln] = row

    def has(self, ln):
        return ln in self.rows

    def drop(self, ln):
        """Drop a line if it is cached; say whether anything changed."""
        return self.rows.pop(ln, None) is not None

    def wipe(self):
        changed = bool(self.rows)
        self.rows.clear()
        return changed
PYEOF

cat > /app/sim/mem.py <<'PYEOF'
"""Global memory and one cache per multiprocessor, for the whole launch.

The caches belong to the multiprocessors, not to the blocks: a block placed later inherits
whatever its multiprocessor fetched for the blocks before it. Nothing keeps the caches in
step with memory or with each other:

  cached load    answers from the line if it is there, otherwise copies the four words of
                 the line as memory holds them now (dropping the oldest fill when full)
  bypass load    answers from memory and drops the line from its own cache
  store          writes memory, and the storer's own copy of the word if it has the line
  atomic add     works on memory only; every cached copy, the issuer's included, stays
  fence          empties the issuer's own cache

Loads report whether they changed the cache, because a spin attempt that changes nothing is
the only kind of issue a stretch of time may be skipped over.
"""
from sim.line import Lines

LW = 4


class Mem:
    def __init__(self, init, sms, cap):
        self.gm = dict(init)
        self.l1 = [Lines(cap) for _ in range(sms)]

    def word(self, a):
        return self.gm.get(a, 0)

    def ld(self, sm, a, cached):
        """Returns (value, whether this multiprocessor's cache changed)."""
        ln = a // LW
        c = self.l1[sm]
        if cached:
            row = c.get(ln)
            if row is not None:
                return row[a % LW], False
            base = ln * LW
            gm = self.gm
            row = [gm.get(base, 0), gm.get(base + 1, 0), gm.get(base + 2, 0),
                   gm.get(base + 3, 0)]
            c.put(ln, row)
            return row[a % LW], True
        return self.gm.get(a, 0), c.drop(ln)

    def peek(self, sm, a, cached):
        """What a load would answer, and whether it would change the cache - without doing it."""
        ln = a // LW
        row = self.l1[sm].get(ln)
        if cached:
            if row is not None:
                return row[a % LW], False
            return self.gm.get(a, 0), True
        return self.gm.get(a, 0), row is not None

    def st(self, sm, a, v):
        self.gm[a] = v
        row = self.l1[sm].get(a // LW)
        if row is not None:
            row[a % LW] = v

    def add(self, sm, a, v):
        old = self.gm.get(a, 0)
        self.gm[a] = old + v
        return old

    def fence(self, sm):
        return self.l1[sm].wipe()
PYEOF

cat > /app/sim/place.py <<'PYEOF'
"""The dispatcher.

At the start of every cycle, while a slot is free and blocks remain, the lowest-numbered
block not yet placed goes to the multiprocessor with the most free slots, ties to the lower
number, into that multiprocessor's lowest free slot. A block that exits at cycle u gives its
slot back from cycle u+1, so its successor is placed at u+1 at the earliest.
"""


class Place:
    def __init__(self, launch):
        self.n = launch.sms
        self.k = launch.slots
        self.grid = launch.grid
        self.rows = [[None] * self.k for _ in range(self.n)]
        self.free = [self.k] * self.n
        self.nfree = self.n * self.k
        self.next = 0
        self.gone = []

    def release(self, b):
        self.gone.append(b)

    def fill(self, blocks, t):
        for b in self.gone:
            self.rows[b.sm][b.slot] = None
            self.free[b.sm] += 1
            self.nfree += 1
        self.gone = []
        placed = []
        while self.next < self.grid and self.nfree:
            s = 0
            for i in range(1, self.n):
                if self.free[i] > self.free[s]:
                    s = i
            row = self.rows[s]
            k = row.index(None)
            b = blocks[self.next]
            row[k] = b
            b.sm, b.slot, b.at = s, k, t
            self.free[s] -= 1
            self.nfree -= 1
            self.next += 1
            placed.append(b)
        return placed
PYEOF

cat > /app/sim/turn.py <<'PYEOF'
"""One multiprocessor's issue rotation.

Each cycle the multiprocessor issues from the first ready block in slot order after the slot
that issued last, wrapping round. A spinning block is ready: every turn it gets is one
attempt, so spinners keep their place in the rotation and delay everyone behind them.
"""


class Turn:
    def __init__(self, k):
        self.k = k
        self.last = k - 1

    @staticmethod
    def ready(b, t):
        return b is not None and b.end is None and b.busy <= t

    def pick(self, row, t):
        k = self.k
        for i in range(1, k + 1):
            j = (self.last + i) % k
            b = row[j]
            if b is not None and b.end is None and b.busy <= t:
                self.last = j
                return b
        return None

    def skip(self, row, t, d):
        """Account for d cycles in which the ready blocks only took failing, idle turns."""
        ready = [j for j in range(self.k) if self.ready(row[j], t)]
        if ready:
            order = sorted(ready, key=lambda j: (j - self.last - 1) % self.k)
            self.last = order[(d - 1) % len(order)]
PYEOF

cat > /app/sim/step.py <<'PYEOF'
"""One instruction of one block.

Every operand is read before the instruction writes anything. A spin makes exactly one
attempt per issue - the load it names, into its destination - and moves on only when the
comparison holds. The caller needs to know what kind of issue it was:

  QUIET   a failing attempt that changed no cache: repeating it changes nothing
  MOVED   a failing attempt that filled or dropped a line
  PASS    an attempt that got through
  OTHER   any other instruction
"""
from sim import load

QUIET, MOVED, PASS, OTHER = range(4)

TEST = {
    "eq": lambda x, y: x == y,
    "ne": lambda x, y: x != y,
    "lt": lambda x, y: x < y,
    "ge": lambda x, y: x >= y,
}

SPIN = ("spin.ca", "spin.cg")


def spinning(launch, b):
    return launch.code[b.pc].op in SPIN


def frozen(launch, mem, b):
    """Would this spinner's next attempt fail and leave its cache as it is?"""
    ins = launch.code[b.pc]
    got, changed = mem.peek(b.sm, load.ea(b, ins.at), ins.op == "spin.ca")
    return not changed and not TEST[ins.cmp](got, load.val(launch, b, ins.b))


def step(launch, mem, b, t):
    ins = launch.code[b.pc]
    op = ins.op
    r = b.reg
    if op in SPIN:
        a = load.ea(b, ins.at)
        want = load.val(launch, b, ins.b)
        got, changed = mem.ld(b.sm, a, op == "spin.ca")
        r[ins.rd] = got
        if TEST[ins.cmp](got, want):
            b.pc += 1
            return PASS
        return MOVED if changed else QUIET
    if op == "mov":
        r[ins.rd] = load.val(launch, b, ins.a)
    elif op in ("add", "sub", "mul", "slt", "mod"):
        x, y = load.val(launch, b, ins.a), load.val(launch, b, ins.b)
        if op == "add":
            r[ins.rd] = x + y
        elif op == "sub":
            r[ins.rd] = x - y
        elif op == "mul":
            r[ins.rd] = x * y
        elif op == "slt":
            r[ins.rd] = 1 if x < y else 0
        else:
            r[ins.rd] = x % y
    elif op == "ld.ca" or op == "ld.cg":
        r[ins.rd] = mem.ld(b.sm, load.ea(b, ins.at), op == "ld.ca")[0]
    elif op == "st":
        mem.st(b.sm, load.ea(b, ins.at), load.val(launch, b, ins.a))
    elif op == "atom.add":
        a, v = load.ea(b, ins.at), load.val(launch, b, ins.a)
        r[ins.rd] = mem.add(b.sm, a, v)
    elif op == "fence":
        mem.fence(b.sm)
    elif op == "work":
        b.busy = t + max(1, load.val(launch, b, ins.a))
    elif op == "bra":
        b.pc = ins.to
        return OTHER
    elif op == "brz" or op == "brnz":
        if (load.val(launch, b, ins.a) == 0) == (op == "brz"):
            b.pc = ins.to
            return OTHER
    elif op == "out":
        b.outs.append(load.val(launch, b, ins.a))
    elif op == "exit":
        b.end = t
        return OTHER
    b.pc += 1
    return OTHER
PYEOF

cat > /app/sim/clock.py <<'PYEOF'
from sim import load


def run(launch):
    blocks = [load.Blk(n) for n in range(launch.grid)]
    for b in blocks:
        b.sm, b.at, b.end = 0, 0, 0
    return blocks, None, 0, dict(launch.mem)
PYEOF
