#!/bin/bash
# a store never reaches another multiprocessor's sum in the cycle it is made
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

    def order(self):
        """The cached lines, the one filled earliest first."""
        return list(self.rows)

    def keep(self, lines, fresh):
        """Keep `lines` (cached now, in fill order) and then fill each of `fresh` in turn,
        where fresh maps a line to its words and holds no line of `lines`."""
        rows = self.rows
        new = {ln: rows[ln] for ln in lines}
        new.update(fresh)
        self.rows = new
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

A sum reads whole lines the same two ways. Loads report whether they changed the cache,
because an issue that changes nothing can be repeated without being stepped.

Two things the clock needs besides the loads:

  * a running sum of memory over any range of lines, so that a stretch in which a sum read
    thousands of lines straight from memory can be settled with one lookup. Memory is sparse,
    so words are kept grouped by chunks of lines, with a total per chunk and per line;
  * a hook called with the address of every write before the write lands, so that a clock
    that is carrying some multiprocessor forward without stepping it can settle that
    multiprocessor first if the write is one it would have seen.
"""
from sim.line import Lines

LW = 4
CHUNK = 1 << 12


class Mem:
    def __init__(self, init, sms, cap):
        self.gm = {}
        self.l1 = [Lines(cap) for _ in range(sms)]
        self.chunk = {}           # chunk number -> sum of every word in it
        self.lines = {}           # chunk number -> {line: sum of its words}, lines ever written
        self.before_write = None  # called with (sm, address) ahead of every write
        for a, v in init.items():
            self.put(a, v)

    def word(self, a):
        return self.gm.get(a, 0)

    def words(self, ln):
        gm, base = self.gm, ln * LW
        return [gm.get(base, 0), gm.get(base + 1, 0), gm.get(base + 2, 0), gm.get(base + 3, 0)]

    def put(self, a, v):
        d = v - self.gm.get(a, 0)
        self.gm[a] = v
        if d:
            ln = a // LW
            c = ln // CHUNK
            self.chunk[c] = self.chunk.get(c, 0) + d
            per = self.lines.get(c)
            if per is None:
                per = self.lines[c] = {}
            per[ln] = per.get(ln, 0) + d

    def span(self, lo, hi):
        """The sum of every word of lines lo .. hi-1, as memory holds them now."""
        if hi <= lo:
            return 0
        c0, c1 = lo // CHUNK, (hi - 1) // CHUNK
        total = 0
        first = self.lines.get(c0)
        if first:
            for ln, v in first.items():
                if lo <= ln < hi:
                    total += v
        if c1 == c0:
            return total
        last = self.lines.get(c1)
        if last:
            for ln, v in last.items():
                if ln < hi:
                    total += v
        chunk = self.chunk
        if c1 - c0 - 1 <= len(chunk):
            for c in range(c0 + 1, c1):
                total += chunk.get(c, 0)
        else:
            for c, v in chunk.items():
                if c0 < c < c1:
                    total += v
        return total

    def ld(self, sm, a, cached):
        """Returns (value, whether this multiprocessor's cache changed)."""
        row, changed = self.row(sm, a // LW, cached)
        return row[a % LW], changed

    def row(self, sm, ln, cached):
        """One whole line, read as a load of that kind reads it: (words, changed)."""
        c = self.l1[sm]
        if cached:
            row = c.get(ln)
            if row is not None:
                return row, False
            row = self.words(ln)
            c.put(ln, row)
            return row, True
        return self.words(ln), c.drop(ln)

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
        if self.before_write is not None:
            self.before_write(sm, a)
        self.put(a, v)
        row = self.l1[sm].get(a // LW)
        if row is not None:
            row[a % LW] = v

    def add(self, sm, a, v):
        if self.before_write is not None:
            self.before_write(sm, a)
        old = self.gm.get(a, 0)
        self.put(a, old + v)
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
        if not self.gone and self.next >= self.grid:
            return ()
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
that issued last, wrapping round. A spinning block is ready, and so is a block in the middle
of a sum: every turn it gets is one attempt or one line, so it keeps its place in the rotation
and delays everyone behind it.
"""


class Turn:
    def __init__(self, k):
        self.k = k
        self.last = k - 1

    def pick(self, row, t):
        k = self.k
        for i in range(1, k + 1):
            j = (self.last + i) % k
            b = row[j]
            if b is not None and b.end is None and b.busy <= t:
                self.last = j
                return b
        return None

    def queue(self, row, t):
        """The blocks ready at t, in the order they will issue from t while none joins or leaves."""
        k, out = self.k, []
        for i in range(1, k + 1):
            b = row[(self.last + i) % k]
            if b is not None and b.end is None and b.busy <= t:
                out.append(b)
        return out
PYEOF

cat > /app/sim/step.py <<'PYEOF'
"""One instruction of one block.

Every operand is read before the instruction writes anything. A spin makes exactly one
attempt per issue - the load it names, into its destination - and moves on only when the
comparison holds. A sum reads one line per issue, from the line holding its address upward,
the way the load of the same kind would read it, and keeps a running total on the block; the
issue that reads its last line writes the total to its destination and moves on. The caller
needs to know what kind of issue it was:

  QUIET   a failing attempt that changed no cache: repeating it changes nothing
  MOVED   a failing attempt that filled or dropped a line
  PASS    an attempt that got through
  OTHER   any other instruction, a line of a sum included
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
SUM = ("sum.ca", "sum.cg")


def spinning(launch, b):
    return launch.code[b.pc].op in SPIN


def frozen(launch, mem, b):
    """Would this spinner's next attempt fail and leave its cache as it is?"""
    ins = launch.code[b.pc]
    got, changed = mem.peek(b.sm, load.ea(b, ins.at), ins.op == "spin.ca")
    return not changed and not TEST[ins.cmp](got, load.val(launch, b, ins.b))


def begin_sum(b, ins):
    """The state a sum starts from at its first issue: next line, lines left, total."""
    if b.left == 0:
        b.line = load.ea(b, ins.at) // 4
        b.left = ins.b[1]
        b.acc = 0


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
    if op in SUM:
        begin_sum(b, ins)
        row, _ = mem.row(b.sm, b.line, op == "sum.ca")
        b.acc += row[0] + row[1] + row[2] + row[3]
        b.line += 1
        b.left -= 1
        if b.left == 0:
            r[ins.rd] = b.acc
            b.pc += 1
        return OTHER
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
"""The clock: one launch, cycle by cycle, except where a multiprocessor can be carried forward
without being stepped.

Each cycle: blocks whose work has run out are ready again; the dispatcher fills free slots;
then the multiprocessors, in number order, issue one instruction each from their rotations.

Lanes. When every ready block on a multiprocessor sits at a sum or a spin, its next cycles are
nothing but lines and attempts taken in rotation. Up to a point that can be computed they are
all regular - every cached sum misses and fills, every bypassing sum reads a line that is not
cached, every attempt fails and changes nothing - and over regular cycles the cache moves only
by fills, first in first out: once the room left at the start is used up, each fill pushes out
the oldest line, so a line cached when the lane opened is gone after a number of fills that
its place in the queue decides. A lane is that run of regular cycles. It is carried forward in
one move when something needs the multiprocessor as it stands:

  * the lane's own end: its first issue that might not be regular, or the one after a sum's
    last line;
  * a block of its own waking or being placed, which changes the rotation;
  * a write the lane would see: to a line one of its sums reads during the lane - always from
    memory, since a sum reaching a cached line ends the lane first - or to the line a bypassing
    spinner of it reads. Nothing else written anywhere reaches it: a cached spinner reads its
    own copy all through the lane. The write lands only after the lane has been carried up to
    it, through the writing cycle itself when the lane's multiprocessor issues first in it.

Carrying a lane forward is arithmetic: over d cycles each of its k blocks issued once in k,
each sum added a range of memory, the cache is its surviving old lines followed by its last
fills, and the rotation sits on the block that issued last.

The hang. A launch hangs at cycle t when from t on every placed block that has not exited sits
at a spin, none is busy, and no attempt ever succeeds. From the first cycle of such a stretch
the machine is closed: no store, no exit, no placement. If it is frozen, it is hung from the
stretch's first cycle. If not, its caches and rotations are all that can change, so it is
stepped until an attempt succeeds (the stretch is over) or a state repeats (it never will),
and the hang is reported at the cycle the stretch began.
"""
import heapq
from bisect import bisect_left, bisect_right, insort

from sim import load
from sim.mem import LW, Mem
from sim.place import Place
from sim.step import PASS, SPIN, TEST, begin_sum, frozen, step
from sim.turn import Turn

NEVER = 1 << 62
CA_SUM, CG_SUM, CA_SPIN, CG_SPIN = range(4)
KIND = {"sum.ca": CA_SUM, "sum.cg": CG_SUM, "spin.ca": CA_SPIN, "spin.cg": CG_SPIN}


class Lane:
    """The regular cycles ahead of one multiprocessor, from t0 up to but not including end."""
    __slots__ = ("t0", "end", "serial", "blocks", "kinds", "k", "m", "ahead", "base", "old",
                 "room", "reads", "cg", "lo", "hi")


def open_lane(launch, mem, turn, row, s, t0, serial):
    """The lane of multiprocessor s from cycle t0, or None if its first issue is not regular."""
    queue = turn.queue(row, t0)
    if not queue:
        return None
    code = launch.code
    kinds = []
    for b in queue:
        kd = KIND.get(code[b.pc].op)
        if kd is None:
            return None
        kinds.append(kd)
    k = len(queue)
    ahead = [0] * (k + 1)
    for q in range(k):
        ahead[q + 1] = ahead[q] + (kinds[q] == CA_SUM)
    m = ahead[k]
    cache = mem.l1[s]
    old = cache.order()
    room = cache.cap - len(old)
    where = {ln: p for p, ln in enumerate(old)}

    def fills(u):
        return (u // k) * m + ahead[u % k]

    end = NEVER
    base = [0] * k
    sums = []
    for q, b in enumerate(queue):
        if kinds[q] <= CG_SUM:
            begin_sum(b, code[b.pc])
            base[q] = b.line
            sums.append((q, b.line, b.line + b.left))
            end = min(end, q + (b.left - 1) * k + 1)
    if old and sums:
        ordered = sorted(old)
        for q, lo, hi in sums:
            i = bisect_left(ordered, lo)
            while i < len(ordered) and ordered[i] < hi:
                ln = ordered[i]
                u = q + (ln - lo) * k
                if u >= end:
                    break
                if fills(u) < room + where[ln] + 1:
                    end = u
                    break
                i += 1
    for qa, la, ha in sums:
        if kinds[qa] != CA_SUM:
            continue
        for qb, lb, hb in sums:
            first = max(la, lb)
            if qb == qa or first >= min(ha, hb):
                continue
            ub = qb + (first - lb) * k
            if qa + (first - la) * k < ub:
                end = min(end, ub)
    cg = set()
    for q, b in enumerate(queue):
        kd = kinds[q]
        if kd <= CG_SUM:
            continue
        ins = code[b.pc]
        a = load.ea(b, ins.at)
        ln = a // LW
        want = load.val(launch, b, ins.b)
        test = TEST[ins.cmp]
        if kd == CA_SPIN:
            p = where.get(ln)
            if p is None or test(cache.rows[ln][a % LW], want):
                end = min(end, q)
            elif m:
                need = room + p + 1
                end = min(end, q + max(0, -(-(need - ahead[q]) // m)) * k)
        else:
            cg.add(ln)
            if ln in where or test(mem.word(a), want):
                end = min(end, q)
            else:
                for qa, la, ha in sums:
                    if kinds[qa] == CA_SUM and la <= ln < ha:
                        end = min(end, qa + (ln - la) * k)
    if end <= 0:
        return None
    lane = Lane()
    lane.t0, lane.end, lane.serial = t0, (t0 + end if end < NEVER else NEVER), serial
    lane.blocks, lane.kinds, lane.k, lane.m, lane.ahead = queue, kinds, k, m, ahead
    lane.base, lane.old, lane.room = base, old, room
    lane.reads = [(lo, hi) for _, lo, hi in sums]
    lane.cg = cg
    edges = list(cg) + [x for lo, hi in lane.reads for x in (lo, hi - 1)]
    lane.lo, lane.hi = (min(edges), max(edges)) if edges else (1, 0)
    return lane


def run(launch):
    blocks = [load.Blk(n) for n in range(launch.grid)]
    for b in blocks:
        b.busy = 0
        b.slot = None
        b.line = b.left = b.acc = 0
    S = launch.sms
    mem = Mem(launch.mem, S, launch.lines)
    pl = Place(launch)
    rows = pl.rows
    turns = [Turn(launch.slots) for _ in range(S)]
    code = launch.code
    at_spin = [ins.op in SPIN for ins in code] + [False]
    lanes = [None] * S
    ends = []                # (end, serial, sm) of lanes; stale entries are skipped
    wakes = []               # (cycle, block number) of blocks inside a work
    ready = [0] * S          # placed, not exited, not busy
    active = set()           # multiprocessors with no lane and a ready block: they issue now
    live = spin = 0
    serial = 0
    now = 0
    index = [None]           # (starts, spans, reach) over every open lane's sum ranges
    shut = []                # lanes closed by a write during the current issue

    def refresh(s):
        if lanes[s] is None and ready[s]:
            active.add(s)
        else:
            active.discard(s)

    def close(s, x):
        """Carry multiprocessor s's lane through every cycle before x, then drop it."""
        nonlocal spin
        lane = lanes[s]
        lanes[s] = None
        index[0] = None
        refresh(s)
        d = x - lane.t0
        if d <= 0:
            return
        k = lane.k
        for q in range(min(k, d)):
            b = lane.blocks[q]
            n = (d - 1 - q) // k + 1
            kd = lane.kinds[q]
            if kd <= CG_SUM:
                b.acc += mem.span(b.line, b.line + n)
                b.line += n
                b.left -= n
                if b.left == 0:
                    b.reg[code[b.pc].rd] = b.acc
                    b.pc += 1
                    spin += at_spin[b.pc]
            else:
                ins = code[b.pc]
                a = load.ea(b, ins.at)
                if kd == CA_SPIN:
                    b.reg[ins.rd] = mem.l1[s].rows[a // LW][a % LW]
                else:
                    b.reg[ins.rd] = mem.word(a)
        m = lane.m
        if m:
            F = (d // k) * m + lane.ahead[d % k]
            cap = mem.l1[s].cap
            cas = [q for q in range(k) if lane.kinds[q] == CA_SUM]
            fresh = {}
            for f in range(max(1, F - cap + 1), F + 1):
                r, i = divmod(f - 1, m)
                ln = lane.base[cas[i]] + r
                fresh[ln] = mem.words(ln)
            gone = min(len(lane.old), max(0, F - lane.room))
            mem.l1[s].keep(lane.old[gone:], fresh)
        turns[s].last = lane.blocks[(d - 1) % k].slot

    def reindex():
        spans = sorted((lo, hi, j) for j, lane in enumerate(lanes) if lane is not None
                       for lo, hi in lane.reads)
        reach, top = [], None
        for lo, hi, j in spans:
            top = hi if top is None or hi > top else top
            reach.append(top)
        index[0] = ([x[0] for x in spans], spans, reach)
        return index[0]

    def before_write(sm, a):
        """A write is about to land: carry up to it every lane that would see it."""
        ln = a // LW
        hit = set()
        for j in range(S):
            lane = lanes[j]
            if lane is not None and j != sm and ln in lane.cg:
                hit.add(j)
        starts, spans, reach = index[0] or reindex()
        i = bisect_right(starts, ln) - 1
        while i >= 0 and reach[i] > ln:
            lo, hi, j = spans[i]
            if ln < hi and j != sm:
                hit.add(j)
            i -= 1
        for j in hit:
            close(j, now + 1)

    mem.before_write = before_write

    def all_frozen():
        for s in range(S):
            for b in rows[s]:
                if b is not None and b.end is None and b.busy <= now:
                    if not at_spin[b.pc] or not frozen(launch, mem, b):
                        return False
        return True

    def snapshot():
        return (tuple(tuple((ln, tuple(w)) for ln, w in c.rows.items()) for c in mem.l1),
                tuple(tu.last for tu in turns))

    t = 0
    phase, seen = None, None
    while True:
        now = t
        while wakes and wakes[0][0] <= t:
            b = blocks[heapq.heappop(wakes)[1]]
            s = b.sm
            ready[s] += 1
            lane = lanes[s]
            if lane is not None and b not in lane.blocks:
                close(s, t)
            refresh(s)
        for b in pl.fill(blocks, t):
            s = b.sm
            live += 1
            spin += at_spin[b.pc]
            ready[s] += 1
            if lanes[s] is not None:
                close(s, t)
            refresh(s)
        if live == 0 and pl.next == launch.grid:
            return blocks, None, 0, mem.gm
        while ends and ends[0][0] <= t:
            _, num, s = heapq.heappop(ends)
            if lanes[s] is not None and lanes[s].serial == num:
                close(s, t)
        stepping = spin == live and not wakes
        if stepping:
            for s in range(S):
                if lanes[s] is not None:
                    close(s, t)
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
        if not active:
            nxt = wakes[0][0] if wakes else NEVER
            while ends and (lanes[ends[0][2]] is None or lanes[ends[0][2]].serial != ends[0][1]):
                heapq.heappop(ends)
            if ends and ends[0][0] < nxt:
                nxt = ends[0][0]
            t = nxt
            continue
        order = sorted(active)
        issued = []
        i = 0
        while i < len(order):
            s = order[i]
            i += 1
            b = turns[s].pick(rows[s], t)
            was = at_spin[b.pc]
            if step(launch, mem, b, t) == PASS:
                phase = None
            if b.end is not None:
                live -= 1
                spin -= was
                ready[s] -= 1
                pl.release(b)
                refresh(s)
            else:
                if b.busy > t:
                    heapq.heappush(wakes, (b.busy, b.n))
                    ready[s] -= 1
                    refresh(s)
                spin += at_spin[b.pc] - was
            issued.append((s, b))
            if shut:
                for j in shut:
                    if j > s and j not in order:
                        insort(order, j)
                del shut[:]
        if not stepping:
            for s, b in issued:
                if lanes[s] is not None or not ready[s]:
                    continue
                if b.end is None and b.busy <= t + 1 and code[b.pc].op not in KIND:
                    continue
                serial += 1
                lane = open_lane(launch, mem, turns[s], rows[s], s, t + 1, serial)
                if lane is not None:
                    lanes[s] = lane
                    index[0] = None
                    active.discard(s)
                    if lane.end < NEVER:
                        heapq.heappush(ends, (lane.end, serial, s))
        t += 1
        if stepping or len(active) != 1:
            continue
        # One multiprocessor issues and nothing else can happen before the next wake or lane
        # end: its cycles need none of the bookkeeping above, until it writes (a write may
        # reach another multiprocessor's lane, which must then issue in the same cycle), a slot
        # is waiting to be filled, or every block left is spinning.
        (s,) = active
        horizon = wakes[0][0] if wakes else NEVER
        while ends and (lanes[ends[0][2]] is None or lanes[ends[0][2]].serial != ends[0][1]):
            heapq.heappop(ends)
        if ends and ends[0][0] < horizon:
            horizon = ends[0][0]
        row, turn = rows[s], turns[s]
        while t < horizon and ready[s] and lanes[s] is None and not pl.gone and spin < live:
            was_last = turn.last
            b = turn.pick(row, t)
            op = code[b.pc].op
            if op == "st" or op == "atom.add":
                turn.last = was_last        # not issued here: the full cycle issues it
                break
            was = at_spin[b.pc]
            now = t
            step(launch, mem, b, t)
            if b.end is not None:
                live -= 1
                spin -= was
                ready[s] -= 1
                pl.release(b)
                refresh(s)
                t += 1
                break
            if b.busy > t:
                heapq.heappush(wakes, (b.busy, b.n))
                ready[s] -= 1
                refresh(s)
                if b.busy < horizon:
                    horizon = b.busy
            spin += at_spin[b.pc] - was
            t += 1
            if ready[s] and (b.busy >= t + 1 or code[b.pc].op in KIND):
                serial += 1
                lane = open_lane(launch, mem, turn, row, s, t, serial)
                if lane is not None:
                    lanes[s] = lane
                    index[0] = None
                    active.discard(s)
                    if lane.end < NEVER:
                        heapq.heappush(ends, (lane.end, serial, s))
PYEOF
