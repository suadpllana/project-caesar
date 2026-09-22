#!/bin/bash
# a placed block first issues on the next cycle
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
"""The clock: one launch, cycle by cycle, with two exact shortcuts.

Each cycle: blocks whose work has run out are ready again; the dispatcher fills free slots;
then the multiprocessors, in number order, issue one instruction each from their rotations.

Shortcut one - a frozen stretch. When every ready block is at a spin whose attempt would fail
and change no cache (a cached spin on a line that is there, a bypassing spin on a line that is
not), and some block is busy, nothing can change until the next block comes out of its work:
no store happens, no cache moves, every attempt repeats the one before. The only thing that
moves is each rotation, one ready block per cycle, so the clock jumps to that wake and every
rotation advances by the length of the jump over its spinners. A stretch where some attempt
misses or drops a line is not frozen - a miss can push another spinner's line out - and is
stepped. Checking is cheap only after a cycle made entirely of idle attempts, so that is when
it is checked; stepping one more cycle is always exact.

Shortcut two - the hang. A launch hangs at cycle t when from t on every placed block that has
not exited sits at a spin, none is busy, and no attempt ever succeeds. From the first cycle
of such a stretch the machine is closed: no store, no exit, no placement. If it is frozen, it
is hung from the stretch's first cycle. If not, its caches and rotations are all that can
change, so it is stepped until an attempt succeeds (the stretch is over) or a state repeats
(it never will), and the hang is reported at the cycle the stretch began.
"""
import heapq

from sim import load
from sim.mem import Mem
from sim.place import Place
from sim.step import MOVED, OTHER, PASS, QUIET, frozen, spinning, step
from sim.turn import Turn


def run(launch):
    blocks = [load.Blk(n) for n in range(launch.grid)]
    for b in blocks:
        b.busy = 0
        b.slot = None
    mem = Mem(launch.mem, launch.sms, launch.lines)
    pl = Place(launch)
    rows = pl.rows
    turns = [Turn(launch.slots) for _ in range(launch.sms)]
    sms = range(launch.sms)
    wakes = []
    live = 0
    spin = 0
    t = 0
    phase, seen = None, None
    quiet = False

    def ready_any():
        for row in rows:
            for b in row:
                if b is not None and b.end is None and b.busy <= t:
                    return True
        return False

    def all_frozen():
        for s in sms:
            for b in rows[s]:
                if b is not None and b.end is None and b.busy <= t:
                    if not spinning(launch, b) or not frozen(launch, mem, b):
                        return False
        return True

    def snapshot():
        return (tuple(tuple((ln, tuple(w)) for ln, w in c.rows.items()) for c in mem.l1),
                tuple(tu.last for tu in turns))

    while True:
        while wakes and wakes[0] <= t:
            heapq.heappop(wakes)
        for b in pl.fill(blocks, t):
            live += 1
            b.busy = t + 1
            heapq.heappush(wakes, t + 1)
            spin += spinning(launch, b)
            quiet = False
        if live == 0 and pl.next == launch.grid:
            return blocks, None, 0, mem.gm
        if spin == live and not wakes:
            if phase is None:
                phase, seen = t, set()
            if all_frozen():
                return blocks, phase, launch.grid - pl.next, mem.gm
            key = snapshot()
            if key in seen:
                return blocks, phase, launch.grid - pl.next, mem.gm
            seen.add(key)
        else:
            phase = None
            if not ready_any():
                t = wakes[0]
                continue
            if quiet and wakes and all_frozen():
                d = wakes[0] - t
                for s in sms:
                    turns[s].skip(rows[s], t, d)
                t = wakes[0]
                continue
        quiet = True
        for s in sms:
            b = turns[s].pick(rows[s], t)
            if b is None:
                continue
            was = spinning(launch, b)
            what = step(launch, mem, b, t)
            if what != QUIET:
                quiet = False
                if what == PASS:
                    phase = None
                if b.end is not None:
                    live -= 1
                    pl.release(b)
                    spin -= was
                    continue
                if b.busy > t:
                    heapq.heappush(wakes, b.busy)
                spin += spinning(launch, b) - was
        t += 1
PYEOF
