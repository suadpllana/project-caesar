"""The sealed model of the launch machine, written apart from the reference solution.

This file is the definition of correct for every graded launch. It has its own parser and
its own clock and shares no code with the tree the agent repairs, so a mistake shared by
the two would have to be made twice, independently.

The machine, as the instruction states it:

  device      S multiprocessors, each holding at most R blocks, each caching at most C lines
              of four words over global memory (line k is words 4k..4k+3)
  each cycle  1. blocks whose work has run out are ready again
              2. while a slot is free and blocks remain, the lowest-numbered block not yet
                 placed goes to the multiprocessor with the most free slots (ties to the
                 lower number), into its lowest free slot; a slot whose block exited at
                 cycle u is free from cycle u+1, and a block placed at t may issue at t
              3. multiprocessors in number order issue at most one instruction each, from
                 the first ready block in slot order after the slot that issued last there
                 (slot 0 first); every effect is complete before the next one issues
  caches      ld.ca answers from the cached line, or fills it with the four words of global
              memory as they stand, dropping the line filled earliest when C lines are held
              (hits never reorder); ld.cg answers from global memory and drops its line from
              its own multiprocessor's cache; st writes global memory and the storer's cached
              copy if the line is there; atom.add touches no cache; fence empties its own
              cache; caches are never emptied by blocks arriving or leaving
  spin        one attempt per issue: the matching load into rd, then on to the next
              instruction only if the comparison holds
  sum         n issues, one line each, starting at the line holding the address as it stands
              at the first issue: each issue reads its line the way the matching load would
              (sum.ca from the cached copy or by filling it, sum.cg from memory, dropping a
              cached copy) and adds its four words; the n-th issue writes the total to rd and
              moves the block on. A block at a sum is ready and is not at a spin.
  hang        at cycle t when, from t on, every placed block that has not exited sits at a
              spin, none is busy, and no attempt at or after t succeeds

How this clock gets through the scale families, exactly:

  * A multiprocessor whose ready blocks all sit at sums or spins gets a plan: the cycles over
    which every issue on it is regular - a cached sum missing and filling, a bypassing sum
    reading a line that is not cached, a spin attempt failing and leaving the cache as it was.
    Over a plan the cache moves only by the cached sums' fills, first in first out, so which
    line is cached at any issue is arithmetic on the number of fills before it, and each sum's
    total is a range sum of memory. The plan stops, conservatively, at the first issue that
    might not be regular, at a sum's last issue, and at anything the multiprocessor cannot see
    coming: a block of its own waking or being placed, or a store it can observe.
  * A store is observable by a plan when it writes a line one of the plan's sums reads from
    memory during the plan, or the line a bypassing spinner of the plan reads; a cached
    spinner's line stays cached for the whole plan, so no store elsewhere reaches it. Before
    such a store lands, the plan is carried up to it - through the storing cycle when the
    planned multiprocessor issues before the storing one - so that every line it had already
    read keeps the value it read and every line after sees the store.
  * An all-spinning stretch with nothing busy is stepped, and its snapshots (caches in fill
    order, rotations) are remembered; a frozen one, or a repeat, means no attempt will ever
    succeed, and the hang is dated from the stretch's first cycle.

A spinner's destination register is never read while it spins (the parser forbids it as the
address register and as the compared value), and a sum writes rd only at its last issue.
"""
import heapq

CMP = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "lt": lambda a, b: a < b,
    "ge": lambda a, b: a >= b,
}
SPINS = ("spin.ca", "spin.cg")
SUMS = ("sum.ca", "sum.cg")
PLANNED = SUMS + SPINS
STEP_CAP = 40_000_000     # cycles in which some multiprocessor issued; no graded launch nears it
ARITH = ("add", "sub", "mul", "slt")
NEVER = 1 << 62

# How a plan treats the device (the scale gate is measured with the other two):
#   "local"  a plan survives everything its multiprocessor cannot observe
#   "device" a plan survives only while no multiprocessor issues anything but regular issues:
#            any other issue anywhere carries every plan up to that cycle
#   "spins"  plans hold spinners only; every sum issue is stepped
MODE = "local"


class BadLaunch(ValueError):
    pass


def _reg(tok):
    if len(tok) == 2 and tok[0] == "r" and tok[1] in "01234567":
        return int(tok[1])
    raise BadLaunch("not a register: %r" % tok)


def _value(tok):
    """A value operand: a register, an integer, or one of the three specials."""
    if tok in ("%bid", "%sm", "%nb"):
        return ("s", tok)
    if tok.startswith("r"):
        return ("r", _reg(tok))
    try:
        return ("i", int(tok))
    except ValueError:
        raise BadLaunch("not a value: %r" % tok)


def _address(tok):
    """[rN], [rN+k] or [k], with k a non-negative integer."""
    if not (tok.startswith("[") and tok.endswith("]")):
        raise BadLaunch("not an address: %r" % tok)
    body = tok[1:-1]
    if body.startswith("r"):
        if "+" in body:
            r, k = body.split("+", 1)
            return (_reg(r), int(k))
        return (_reg(body), 0)
    return (None, int(body))


def parse(lines):
    dev = grid = None
    mem, show, prog = {}, [], None
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        if prog is not None:
            prog.append(s)
            continue
        f = s.split()
        if f[0] == "dev":
            dev = tuple(int(x) for x in f[1:4])
        elif f[0] == "grid":
            grid = int(f[1])
        elif f[0] == "mem":
            mem[int(f[1])] = int(f[2])
        elif f[0] == "show":
            show.extend(int(x) for x in f[1:])
        elif f[0] == "prog":
            prog = []
        else:
            raise BadLaunch("unknown header line: %r" % s)
    if dev is None or grid is None or prog is None:
        raise BadLaunch("a launch needs dev, grid and prog")

    labels, raw_code = {}, []
    for s in prog:
        if s.endswith(":"):
            labels[s[:-1]] = len(raw_code)
        else:
            raw_code.append(s.split())

    def target(name):
        if name not in labels:
            raise BadLaunch("no label %r" % name)
        return labels[name]

    code = []
    for f in raw_code:
        op, a = f[0], f[1:]
        if op == "mov":
            code.append(("mov", _reg(a[0]), _value(a[1])))
        elif op in ARITH:
            code.append((op, _reg(a[0]), _value(a[1]), _value(a[2])))
        elif op == "mod":
            k = int(a[2])
            if k <= 0:
                raise BadLaunch("mod needs a positive literal")
            code.append(("mod", _reg(a[0]), _value(a[1]), k))
        elif op in ("ld.ca", "ld.cg"):
            code.append((op, _reg(a[0]), _address(a[1])))
        elif op == "st":
            code.append(("st", _address(a[0]), _value(a[1])))
        elif op == "atom.add":
            code.append(("atom.add", _reg(a[0]), _address(a[1]), _value(a[2])))
        elif op == "fence":
            code.append(("fence",))
        elif op in SPINS:
            rd, adr, cmp, v = _reg(a[0]), _address(a[1]), a[2], _value(a[3])
            if cmp not in CMP:
                raise BadLaunch("unknown comparison %r" % cmp)
            if adr[0] == rd or v == ("r", rd):
                raise BadLaunch("a spin may not read its own destination register")
            code.append((op, rd, adr, cmp, v))
        elif op in SUMS:
            n = int(a[2])
            if n <= 0:
                raise BadLaunch("a sum needs a positive literal count")
            code.append((op, _reg(a[0]), _address(a[1]), n))
        elif op == "work":
            code.append(("work", _value(a[0])))
        elif op == "bra":
            code.append(("bra", target(a[0])))
        elif op in ("brz", "brnz"):
            code.append((op, _value(a[0]), target(a[1])))
        elif op == "out":
            code.append(("out", _value(a[0])))
        elif op == "exit":
            code.append(("exit",))
        else:
            raise BadLaunch("unknown instruction %r" % op)
    return dev, grid, mem, show, code


class LineSums:
    """Sums of global memory over ranges of lines, current as words change.

    A Fenwick tree over line numbers 0 .. 2**30-1, held in a dict so that only the nodes a
    store touches exist. Lines outside that span are kept apart and summed by scanning.
    """
    SPAN = 1 << 30

    def __init__(self):
        self.tree = {}
        self.far = {}

    def add(self, line, v):
        if not 0 <= line < self.SPAN:
            self.far[line] = self.far.get(line, 0) + v
            return
        i, tree, top = line + 1, self.tree, self.SPAN
        while i <= top:
            tree[i] = tree.get(i, 0) + v
            i += i & -i

    def _below(self, line):
        i = min(max(line, 0), self.SPAN)
        tree, s = self.tree, 0
        while i > 0:
            s += tree.get(i, 0)
            i -= i & -i
        return s

    def span(self, lo, hi):
        """Sum of the words of lines lo .. hi-1."""
        s = self._below(hi) - self._below(lo)
        for line, v in self.far.items():
            if lo <= line < hi:
                s += v
        return s


class Plan:
    """The regular issues ahead of one multiprocessor, from cycle t0 up to cycle h."""
    __slots__ = ("t0", "h", "order", "kind", "k", "line0", "left0", "m", "cpre", "q0",
                 "reads", "watch", "members", "lo", "hi")


class Machine:
    """One launch. Blocks are numbered 0..G-1 and live in parallel lists."""

    def __init__(self, dev, grid, mem, code, mode=None):
        self.S, self.R, self.C = dev
        self.G = grid
        self.code = code
        self.spin_at = [ins[0] in SPINS for ins in code] + [False]
        self.mode = mode or MODE
        self.gm = dict(mem)
        self.sums = LineSums()
        for a, v in mem.items():
            if v:
                self.sums.add(a // 4, v)
        self.cache = [dict() for _ in range(self.S)]   # insertion order is fill order
        self.slot = [[None] * self.R for _ in range(self.S)]
        self.last = [self.R - 1] * self.S
        self.nready = [0] * self.S
        self.plan = [None] * self.S
        self.horizons = []        # (h, sm, serial, plan) - stale entries are skipped
        self.made = 0
        G = grid
        self.pc = [0] * G
        self.reg = [[0] * 8 for _ in range(G)]
        self.outs = [[] for _ in range(G)]
        self.sm = [None] * G
        self.slotof = [None] * G
        self.placed = [None] * G
        self.ended = [None] * G
        self.busy = [0] * G
        self.sline = [0] * G      # a sum in progress: the next line, the lines left, the total
        self.sleft = [0] * G
        self.sacc = [0] * G
        self.heap = []            # (busy until, block) for blocks inside a work
        self.nxt = 0              # lowest block not yet placed
        self.live = 0             # placed and not exited
        self.at_spin = 0          # live blocks whose pc points at a spin
        self.freeing = []         # (sm, slot) that become free next cycle
        self.nfree = self.S * self.R

    # -- operands ---------------------------------------------------------------------

    def val(self, b, v):
        kind, x = v
        if kind == "r":
            return self.reg[b][x]
        if kind == "i":
            return x
        if x == "%bid":
            return b
        if x == "%sm":
            return self.sm[b]
        return self.G

    def ea(self, b, adr):
        r, k = adr
        return (self.reg[b][r] if r is not None else 0) + k

    def is_spin(self, pc):
        return self.spin_at[pc]

    def set_pc(self, b, new):
        was = self.spin_at[self.pc[b]]
        now = self.spin_at[new]
        self.pc[b] = new
        if was != now:
            self.at_spin += 1 if now else -1

    # -- memory -------------------------------------------------------------------------

    def words(self, line):
        base, gm = 4 * line, self.gm
        return [gm.get(base, 0), gm.get(base + 1, 0), gm.get(base + 2, 0), gm.get(base + 3, 0)]

    def read_line(self, s, cached, line):
        """One line read the way a load of that kind reads it. Returns (words, changed)."""
        c = self.cache[s]
        if cached:
            row = c.get(line)
            if row is not None:
                return row, False
            if len(c) >= self.C:
                del c[next(iter(c))]
            row = self.words(line)
            c[line] = row
            return row, True
        row = self.words(line)
        if line in c:
            del c[line]
            return row, True
        return row, False

    def write(self, a, v):
        old = self.gm.get(a, 0)
        self.gm[a] = v
        if v != old:
            self.sums.add(a // 4, v - old)

    def attempt_is_frozen(self, b, s):
        """Would this spinner's next attempt fail and leave every cache as it is?"""
        op, rd, adr, cmp, v = self.code[self.pc[b]]
        a = self.ea(b, adr)
        line, w = a // 4, a % 4
        c = self.cache[s]
        want = self.val(b, v)
        if op == "spin.ca":
            return line in c and not CMP[cmp](c[line][w], want)
        return line not in c and not CMP[cmp](self.gm.get(a, 0), want)

    # -- one instruction ------------------------------------------------------------------

    def issue(self, b, s, t):
        """Execute block b's next instruction on multiprocessor s at cycle t.

        Returns "quiet" for a failing spin attempt that changed no cache, "moved" for a
        failing attempt that filled or dropped a line, "success" for an attempt that got
        through, and "other" for every other instruction. A write to global memory is shown to
        every plan that can observe it before it lands.
        """
        ins = self.code[self.pc[b]]
        op = ins[0]
        r = self.reg[b]
        if op == "mov":
            r[ins[1]] = self.val(b, ins[2])
        elif op in ARITH:
            x, y = self.val(b, ins[2]), self.val(b, ins[3])
            if op == "add":
                r[ins[1]] = x + y
            elif op == "sub":
                r[ins[1]] = x - y
            elif op == "mul":
                r[ins[1]] = x * y
            else:
                r[ins[1]] = 1 if x < y else 0
        elif op == "mod":
            r[ins[1]] = self.val(b, ins[2]) % ins[3]
        elif op in ("ld.ca", "ld.cg"):
            a = self.ea(b, ins[2])
            row, _ = self.read_line(s, op == "ld.ca", a // 4)
            r[ins[1]] = row[a % 4]
        elif op == "st":
            a, v = self.ea(b, ins[1]), self.val(b, ins[2])
            self.observe(s, a, t)
            self.write(a, v)
            row = self.cache[s].get(a // 4)
            if row is not None:
                row[a % 4] = v
        elif op == "atom.add":
            a, v = self.ea(b, ins[2]), self.val(b, ins[3])
            self.observe(s, a, t)
            old = self.gm.get(a, 0)
            self.write(a, old + v)
            r[ins[1]] = old
        elif op == "fence":
            self.cache[s].clear()
        elif op in SPINS:
            _, rd, adr, cmp, v = ins
            a, want = self.ea(b, adr), self.val(b, v)
            row, changed = self.read_line(s, op == "spin.ca", a // 4)
            got = row[a % 4]
            r[rd] = got
            if CMP[cmp](got, want):
                self.set_pc(b, self.pc[b] + 1)
                return "success"
            return "moved" if changed else "quiet"
        elif op in SUMS:
            _, rd, adr, n = ins
            if self.sleft[b] == 0:
                self.sline[b] = self.ea(b, adr) // 4
                self.sleft[b] = n
                self.sacc[b] = 0
            line = self.sline[b]
            row, _ = self.read_line(s, op == "sum.ca", line)
            self.sacc[b] += row[0] + row[1] + row[2] + row[3]
            self.sline[b] = line + 1
            self.sleft[b] -= 1
            if self.sleft[b]:
                return "other"
            r[rd] = self.sacc[b]
            self.sacc[b] = 0
        elif op == "work":
            n = max(1, self.val(b, ins[1]))
            self.busy[b] = t + n
            heapq.heappush(self.heap, (t + n, b))
            self.nready[s] -= 1
        elif op == "bra":
            self.set_pc(b, ins[1])
            return "other"
        elif op in ("brz", "brnz"):
            x = self.val(b, ins[1])
            if (x == 0) == (op == "brz"):
                self.set_pc(b, ins[2])
            else:
                self.set_pc(b, self.pc[b] + 1)
            return "other"
        elif op == "out":
            self.outs[b].append(self.val(b, ins[1]))
        elif op == "exit":
            self.ended[b] = t
            self.live -= 1
            self.nready[s] -= 1
            if self.is_spin(self.pc[b]):
                self.at_spin -= 1
            self.freeing.append((s, self.slotof[b]))
            return "other"
        self.set_pc(b, self.pc[b] + 1)
        return "other"

    # -- plans ----------------------------------------------------------------------------

    def ready(self, b, t):
        return b is not None and self.ended[b] is None and self.busy[b] <= t

    def rotation(self, s, t):
        """The ready blocks of multiprocessor s in the order they would issue from cycle t."""
        row, start, R = self.slot[s], self.last[s], self.R
        out = []
        for i in range(1, R + 1):
            b = row[(start + i) % R]
            if b is not None and self.ended[b] is None and self.busy[b] <= t:
                out.append(b)
        return out

    def make_plan(self, s, t0):
        """A plan for multiprocessor s from cycle t0, or None when its next issue is not regular."""
        order = self.rotation(s, t0)
        if not order:
            return None
        k = len(order)
        kind = []
        for b in order:
            op = self.code[self.pc[b]][0]
            if op == "sum.ca":
                kind.append(1)
            elif op == "sum.cg":
                kind.append(2)
            elif op == "spin.ca":
                kind.append(3)
            elif op == "spin.cg":
                kind.append(4)
            else:
                return None
        if self.mode == "spins" and (1 in kind or 2 in kind):
            return None
        C = self.C
        c = self.cache[s]
        q0 = list(c)
        s0 = len(q0)
        where = {line: p for p, line in enumerate(q0)}
        line0 = [0] * k
        left0 = [0] * k
        cpre = [0] * (k + 1)
        for q, b in enumerate(order):
            cpre[q + 1] = cpre[q] + (kind[q] == 1)
            if kind[q] <= 2:
                if self.sleft[b] == 0:
                    ins = self.code[self.pc[b]]
                    self.sline[b] = self.ea(b, ins[2]) // 4
                    self.sleft[b] = ins[3]
                    self.sacc[b] = 0
                line0[q] = self.sline[b]
                left0[q] = self.sleft[b]
        m = cpre[k]

        def fills(u):
            """Fills done by the plan's cached sums before its u-th issue."""
            return (u // k) * m + cpre[u % k]

        def first_turn_at(q, need):
            """The first issue of position q made after `need` fills, or NEVER."""
            if m == 0:
                return NEVER
            # issues of position q are u = q + j*k with fills(u) = j*m + cpre[q]
            j = max(0, -(-(need - cpre[q]) // m))
            return q + j * k

        H = NEVER
        reads, watch = [], set()
        for q in range(k):
            b = order[q]
            kd = kind[q]
            if kd <= 2:
                lo, n = line0[q], left0[q]
                reads.append((lo, lo + n))
                H = min(H, q + (n - 1) * k + 1)          # the sum's last issue
                # an issue on a line cached when the plan starts, while it is still cached
                for p, line in enumerate(q0):
                    if lo <= line < lo + n:
                        u = q + (line - lo) * k
                        if fills(u) < C - s0 + p + 1:
                            H = min(H, u)
                # a line another cached sum of this plan fills before this one reads it
                for q2 in range(k):
                    if q2 == q or kind[q2] != 1:
                        continue
                    lo2, n2 = line0[q2], left0[q2]
                    a, z = max(lo, lo2), min(lo + n, lo2 + n2)
                    if a >= z:
                        continue
                    # the gap between the fill and the read is the same for every shared line
                    if q2 + (a - lo2) * k < q + (a - lo) * k:
                        H = min(H, q + (a - lo) * k)
            else:
                ins = self.code[self.pc[b]]
                a = self.ea(b, ins[2])
                line, w = a // 4, a % 4
                want = self.val(b, ins[4])
                test = CMP[ins[3]]
                if kd == 3:
                    p = where.get(line)
                    if p is None or test(c[line][w], want):
                        H = min(H, q)
                    else:
                        H = min(H, first_turn_at(q, C - s0 + p + 1))
                else:
                    watch.add(line)          # a cached spinner reads its copy, never memory
                    if line in where or test(self.gm.get(a, 0), want):
                        H = min(H, q)
                    else:
                        for q2 in range(k):
                            if kind[q2] == 1 and line0[q2] <= line < line0[q2] + left0[q2]:
                                H = min(H, q2 + (line - line0[q2]) * k)
        if H <= 0:
            return None
        pl = Plan()
        pl.t0, pl.h = t0, (t0 + H if H < NEVER else NEVER)
        pl.order, pl.kind, pl.k = order, kind, k
        pl.line0, pl.left0, pl.m, pl.cpre, pl.q0 = line0, left0, m, cpre, q0
        pl.reads, pl.watch, pl.members = reads, watch, set(order)
        spans = [line for line in watch] + [x for r in reads for x in (r[0], r[1] - 1)]
        pl.lo, pl.hi = (min(spans), max(spans)) if spans else (1, 0)
        return pl

    def settle(self, s, x):
        """Carry multiprocessor s's plan through every cycle before x, then drop it."""
        pl = self.plan[s]
        self.plan[s] = None
        d = x - pl.t0
        if d <= 0:
            return
        k, order = pl.k, pl.order
        for q in range(min(k, d)):
            b = order[q]
            n = (d - q + k - 1) // k
            kd = pl.kind[q]
            if kd <= 2:
                lo = pl.line0[q]
                self.sacc[b] += self.sums.span(lo, lo + n)
                self.sline[b] = lo + n
                self.sleft[b] = pl.left0[q] - n
                if self.sleft[b] == 0:
                    self.reg[b][self.code[self.pc[b]][1]] = self.sacc[b]
                    self.sacc[b] = 0
                    self.set_pc(b, self.pc[b] + 1)
            else:
                ins = self.code[self.pc[b]]
                a = self.ea(b, ins[2])
                if kd == 3:
                    self.reg[b][ins[1]] = self.cache[s][a // 4][a % 4]
                else:
                    self.reg[b][ins[1]] = self.gm.get(a, 0)
        m = pl.m
        if m:
            F = (d // k) * m + pl.cpre[d % k]
            C = self.C
            q0 = pl.q0
            s0 = len(q0)
            gone = min(s0, max(0, F - (C - s0)))
            want = min(F, C)
            new = []                       # the last `want` fills, latest first
            u = d - 1
            while len(new) < want:
                q = u % k
                if pl.kind[q] == 1:
                    new.append(pl.line0[q] + (u - q) // k)
                u -= 1
            old = self.cache[s]
            c = {}
            for line in q0[gone:]:
                c[line] = old[line]
            for line in reversed(new):
                c[line] = self.words(line)
            self.cache[s] = c
        self.last[s] = self.slotof[order[(d - 1) % k]]

    def observe(self, s, a, t):
        """A store to word a by multiprocessor s at cycle t: carry every plan that can see it."""
        line = a // 4
        for j in range(self.S):
            pl = self.plan[j]
            if pl is None or j == s or not pl.lo <= line <= pl.hi:
                continue
            if line in pl.watch or any(lo <= line < hi for lo, hi in pl.reads):
                self.settle(j, t + 1 if j < s else t)

    # -- the clock ------------------------------------------------------------------------

    def place(self, t):
        if not self.freeing and self.nxt >= self.G:
            return ()
        for s, k in self.freeing:
            self.slot[s][k] = None
        self.nfree += len(self.freeing)
        self.freeing = []
        touched = []
        while self.nxt < self.G and self.nfree > 0:
            best, most = -1, 0
            for s in range(self.S):
                free = self.slot[s].count(None)
                if free > most:
                    best, most = s, free
            if best < 0:
                break
            k = self.slot[best].index(None)
            b = self.nxt
            self.slot[best][k] = b
            self.nfree -= 1
            self.sm[b], self.slotof[b], self.placed[b] = best, k, t
            self.live += 1
            self.nready[best] += 1
            if self.is_spin(self.pc[b]):
                self.at_spin += 1
            self.nxt += 1
            touched.append(best)
        return touched

    def frozen(self, t):
        """Every ready block is a spinner whose attempt fails and changes no cache."""
        for s in range(self.S):
            for b in self.slot[s]:
                if self.ready(b, t):
                    if not self.is_spin(self.pc[b]) or not self.attempt_is_frozen(b, s):
                        return False
        return True

    def snapshot(self):
        caches = tuple(tuple((ln, tuple(ws)) for ln, ws in c.items()) for c in self.cache)
        return caches, tuple(self.last)

    def next_event(self):
        best = self.heap[0][0] if self.heap else NEVER
        hz = self.horizons
        while hz and self.plan[hz[0][1]] is not hz[0][3]:
            heapq.heappop(hz)
        if hz and hz[0][0] < best:
            best = hz[0][0]
        return best

    def run(self):
        S = self.S
        t = 0
        steps = 0
        phase, seen = None, None
        hang = None
        device = self.mode == "device"
        while True:
            while self.heap and self.heap[0][0] <= t:
                _, b = heapq.heappop(self.heap)
                if self.ended[b] is None:
                    s = self.sm[b]
                    self.nready[s] += 1
                    pl = self.plan[s]
                    if pl is not None and b not in pl.members:
                        self.settle(s, t)
            touched = self.place(t)
            for s in touched:
                if self.plan[s] is not None:
                    self.settle(s, t)
            if self.live == 0 and self.nxt == self.G:
                break
            stepping = self.at_spin == self.live and not self.heap
            if stepping:
                # every placed block sits at a spin and none is busy
                for s in range(S):
                    if self.plan[s] is not None:
                        self.settle(s, t)
                if phase is None:
                    phase, seen = t, set()
                if self.frozen(t):
                    hang = phase
                    break
                key = self.snapshot()
                if key in seen:
                    hang = phase
                    break
                seen.add(key)
            else:
                phase = None
                if device and any((pl is None and self.nready[s]) or (pl is not None and pl.h <= t)
                                  for s, pl in enumerate(self.plan)):
                    for s in range(S):
                        if self.plan[s] is not None:
                            self.settle(s, t)
            issued = []
            for s in range(S):
                pl = self.plan[s]
                if pl is not None:
                    if pl.h > t:
                        continue
                    self.settle(s, t)
                if not self.nready[s]:
                    continue
                row, start, R = self.slot[s], self.last[s], self.R
                for i in range(1, R + 1):
                    k = (start + i) % R
                    b = row[k]
                    if b is not None and self.ended[b] is None and self.busy[b] <= t:
                        self.last[s] = k
                        if self.issue(b, s, t) == "success":
                            phase = None   # an attempt got through; a hang starts later
                        issued.append((s, b))
                        break
            if not issued:
                # every multiprocessor is idle or inside a plan: go to the next thing that happens
                nxt = self.next_event()
                if nxt >= NEVER:
                    raise BadLaunch("no block can ever issue again")
                t = nxt
                continue
            if not stepping:
                for s, b in issued:
                    if self.plan[s] is not None or not self.nready[s]:
                        continue
                    if (self.ended[b] is None and self.busy[b] <= t + 1
                            and self.code[self.pc[b]][0] not in PLANNED):
                        continue           # the block that just issued cannot be planned
                    pl = self.make_plan(s, t + 1)
                    if pl is not None:
                        self.plan[s] = pl
                        if pl.h < NEVER:
                            self.made += 1
                            heapq.heappush(self.horizons, (pl.h, s, self.made, pl))
            t += 1
            steps += 1
            if steps > STEP_CAP:
                raise BadLaunch("launch ran past %d issuing cycles" % STEP_CAP)
        return hang

    def report(self, hang, show):
        out = []
        for b in range(self.G):
            if self.ended[b] is not None:
                out.append("blk %d sm %d at %d end %d%s" % (
                    b, self.sm[b], self.placed[b], self.ended[b],
                    "".join(" %d" % v for v in self.outs[b])))
        if hang is not None:
            out.append("hang %d" % hang)
            for b in range(self.G):
                if self.placed[b] is not None and self.ended[b] is None:
                    op, rd, adr, cmp, v = self.code[self.pc[b]]
                    out.append("spin %d sm %d at %d on %d%s" % (
                        b, self.sm[b], self.placed[b], self.ea(b, adr),
                        "".join(" %d" % x for x in self.outs[b])))
            out.append("left %d" % (self.G - self.nxt))
        for a in show:
            out.append("mem %d %d" % (a, self.gm.get(a, 0)))
        return out


def expect(lines, mode=None):
    """The lines a correct runner prints for this launch file."""
    dev, grid, mem, show, code = parse(lines)
    m = Machine(dev, grid, mem, code, mode)
    hang = m.run()
    return m.report(hang, show)


# --- the frozen interface -------------------------------------------------------------------

from sim import load as _load  # noqa: E402


def _value(x):
    kind, v = x
    if kind == "r":
        return ("r", v)
    if kind == "k":
        return ("i", v)
    return ("s", kind)


def _ins(ins):
    op = ins.op
    if op == "mov":
        return ("mov", ins.rd, _value(ins.a))
    if op in ARITH:
        return (op, ins.rd, _value(ins.a), _value(ins.b))
    if op == "mod":
        return ("mod", ins.rd, _value(ins.a), ins.b[1])
    if op in ("ld.ca", "ld.cg"):
        return (op, ins.rd, ins.at)
    if op == "st":
        return ("st", ins.at, _value(ins.a))
    if op == "atom.add":
        return ("atom.add", ins.rd, ins.at, _value(ins.a))
    if op in ("fence", "exit"):
        return (op,)
    if op in SPINS:
        return (op, ins.rd, ins.at, ins.cmp, _value(ins.b))
    if op in SUMS:
        return (op, ins.rd, ins.at, ins.b[1])
    if op in ("work", "out"):
        return (op, _value(ins.a))
    if op == "bra":
        return ("bra", ins.to)
    return (op, _value(ins.a), ins.to)


def run(launch):
    code = [_ins(ins) for ins in launch.code]
    m = Machine((launch.sms, launch.slots, launch.lines), launch.grid, launch.mem, code)
    hang = m.run()
    blocks = []
    for n in range(launch.grid):
        b = _load.Blk(n)
        b.sm, b.at, b.end = m.sm[n], m.placed[n], m.ended[n]
        b.outs, b.pc, b.reg = m.outs[n], m.pc[n], m.reg[n]
        blocks.append(b)
    return blocks, hang, (launch.grid - m.nxt if hang is not None else 0), m.gm
