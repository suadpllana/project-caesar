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
  hang        at cycle t when, from t on, every placed block that has not exited sits at a
              spin, none is busy, and no attempt at or after t succeeds

Two things make this fast enough for the scale families, and both are exact:

  * a frozen stretch - every ready block is at a spin whose attempt fails and leaves every
    cache as it was, and some block is busy - changes nothing but the rotations, so the
    clock jumps to the next wake and each rotation advances by the jump over its spinners;
  * an all-spinning stretch that is not frozen is stepped, and its snapshots (caches in fill
    order, rotations) are remembered; a repeat means no attempt will ever succeed.

A spinner's destination register is never read while it spins (the parser forbids it as the
address register and as the compared value), so the jump does not have to replay it.
"""
import heapq

CMP = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "lt": lambda a, b: a < b,
    "ge": lambda a, b: a >= b,
}
SPINS = ("spin.ca", "spin.cg")
STEP_CAP = 40_000_000     # stepped cycles; no graded launch comes near it
ARITH = ("add", "sub", "mul", "slt")


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


class Machine:
    """One launch. Blocks are numbered 0..G-1 and live in parallel lists."""

    def __init__(self, dev, grid, mem, code):
        self.S, self.R, self.C = dev
        self.G = grid
        self.code = code
        self.gm = dict(mem)
        self.cache = [dict() for _ in range(self.S)]   # insertion order is fill order
        self.slot = [[None] * self.R for _ in range(self.S)]
        self.last = [self.R - 1] * self.S
        G = grid
        self.pc = [0] * G
        self.reg = [[0] * 8 for _ in range(G)]
        self.outs = [[] for _ in range(G)]
        self.sm = [None] * G
        self.slotof = [None] * G
        self.placed = [None] * G
        self.ended = [None] * G
        self.busy = [0] * G
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
        return pc < len(self.code) and self.code[pc][0] in SPINS

    def set_pc(self, b, new):
        was = self.is_spin(self.pc[b])
        now = self.is_spin(new)
        self.pc[b] = new
        if was != now:
            self.at_spin += 1 if now else -1

    # -- memory -------------------------------------------------------------------------

    def load(self, s, op, a):
        """One load. Returns (value, whether any cache changed)."""
        line, w = a // 4, a % 4
        c = self.cache[s]
        if op in ("ld.ca", "spin.ca"):
            if line in c:
                return c[line][w], False
            if len(c) >= self.C:
                del c[next(iter(c))]
            base = 4 * line
            c[line] = [self.gm.get(base + i, 0) for i in range(4)]
            return c[line][w], True
        v = self.gm.get(a, 0)
        if line in c:
            del c[line]
            return v, True
        return v, False

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

        Returns what the issue was: "quiet" for a failing spin attempt that changed no
        cache (the only kind of issue a frozen stretch is made of), "moved" for a failing
        attempt that filled or dropped a line, "success" for an attempt that got through,
        and "other" for every other instruction.
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
            r[ins[1]], _ = self.load(s, op, self.ea(b, ins[2]))
        elif op == "st":
            a, v = self.ea(b, ins[1]), self.val(b, ins[2])
            self.gm[a] = v
            c = self.cache[s]
            if a // 4 in c:
                c[a // 4][a % 4] = v
        elif op == "atom.add":
            a, v = self.ea(b, ins[2]), self.val(b, ins[3])
            old = self.gm.get(a, 0)
            self.gm[a] = old + v
            r[ins[1]] = old
        elif op == "fence":
            self.cache[s].clear()
        elif op in SPINS:
            _, rd, adr, cmp, v = ins
            a, want = self.ea(b, adr), self.val(b, v)
            got, changed = self.load(s, op, a)
            r[rd] = got
            if CMP[cmp](got, want):
                self.set_pc(b, self.pc[b] + 1)
                return "success"
            return "moved" if changed else "quiet"
        elif op == "work":
            n = max(1, self.val(b, ins[1]))
            self.busy[b] = t + n
            heapq.heappush(self.heap, (t + n, b))
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
            if self.is_spin(self.pc[b]):
                self.at_spin -= 1
            self.freeing.append((s, self.slotof[b]))
            return "other"
        self.set_pc(b, self.pc[b] + 1)
        return "other"

    # -- the clock ------------------------------------------------------------------------

    def place(self, t):
        for s, k in self.freeing:
            self.slot[s][k] = None
        self.nfree += len(self.freeing)
        self.freeing = []
        placed_any = False
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
            if self.is_spin(self.pc[b]):
                self.at_spin += 1
            self.nxt += 1
            placed_any = True
        return placed_any

    def ready(self, b, t):
        return b is not None and self.ended[b] is None and self.busy[b] <= t

    def frozen(self, t):
        """Every ready block is a spinner whose attempt fails and changes no cache."""
        for s in range(self.S):
            for b in self.slot[s]:
                if self.ready(b, t):
                    if not self.is_spin(self.pc[b]) or not self.attempt_is_frozen(b, s):
                        return False
        return True

    def jump(self, t, until):
        """Skip a frozen stretch [t, until): each rotation passes over its spinners."""
        d = until - t
        for s in range(self.S):
            row = self.slot[s]
            spinners = [k for k in range(self.R) if self.ready(row[k], t)]
            if not spinners:
                continue
            start = self.last[s]
            order = sorted(spinners, key=lambda k: (k - start - 1) % self.R)
            self.last[s] = order[(d - 1) % len(order)]

    def snapshot(self):
        caches = tuple(tuple((ln, tuple(ws)) for ln, ws in c.items()) for c in self.cache)
        return caches, tuple(self.last)

    def run(self):
        t = 0
        steps = 0
        phase, seen = None, None
        quiet = False
        hang = None
        while True:
            while self.heap and self.heap[0][0] <= t:
                heapq.heappop(self.heap)
            if self.place(t):
                quiet = False
            if self.live == 0 and self.nxt == self.G:
                break
            if self.at_spin == self.live and not self.heap:
                # every placed block sits at a spin and none is busy
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
                if not any(self.ready(b, t) for row in self.slot for b in row):
                    t = self.heap[0][0]
                    continue
                if quiet and self.heap and self.frozen(t):
                    until = self.heap[0][0]
                    self.jump(t, until)
                    t = until
                    continue
            quiet = True
            for s in range(self.S):
                row, start = self.slot[s], self.last[s]
                for i in range(1, self.R + 1):
                    k = (start + i) % self.R
                    b = row[k]
                    if self.ready(b, t):
                        self.last[s] = k
                        what = self.issue(b, s, t)
                        if what != "quiet":
                            quiet = False
                        if what == "success":
                            phase = None   # an attempt got through; a hang starts later
                        break
            t += 1
            steps += 1
            if steps > STEP_CAP:
                raise BadLaunch("launch ran past %d stepped cycles" % STEP_CAP)
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


def expect(lines):
    """The lines a correct runner prints for this launch file."""
    dev, grid, mem, show, code = parse(lines)
    m = Machine(dev, grid, mem, code)
    hang = m.run()
    return m.report(hang, show)
