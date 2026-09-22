"""Sealed model of the debugger the task asks for.

This file is the specification written as code, and it is deliberately the slow, literal
form: it owns its own copy of the machine, executes one instruction at a time with the
tape in hand, and applies the stop rules after every instruction. It never plants
anything and never talks to a target, so it shares no structure with an engine that runs
a target to planted addresses - which is the point: the two agree only if both implement
the stated rules.

The rule numbers in the comments are the numbers of the frozen contract in STATE.md, and
each rule has its sentence in instruction.md (see authoring/line-step-stop/trace.md).

Entry point: `play(image_text, tape, commands) -> list[str]`, one line per command.
"""

OPS = ("nop", "set", "in", "dec", "jnz", "jmp", "call", "ret")


class Program:
    """The image, parsed into flat tables indexed by address."""

    def __init__(self, text):
        self.fn_name = []        # per function: name
        self.fn_lo = []
        self.fn_hi = []
        self.fn_has_lines = []
        self.code = []           # per address: (op, arg1, arg2)
        rows = []                # (addr, line, statement)
        inls = []                # (id, fn name, parent token, call line, lo, hi)
        for raw in text.splitlines():
            w = raw.split()
            if not w:
                continue
            if w[0] == "fn":
                self.fn_name.append(w[1])
                self.fn_lo.append(int(w[2]))
                self.fn_hi.append(int(w[3]))
                self.fn_has_lines.append(len(w) > 4)
            elif w[0] == "row":
                rows.append((int(w[1]), int(w[2]), len(w) == 3))
            elif w[0] == "inl":
                inls.append((int(w[1]), w[2], w[3], int(w[4]), int(w[5]), int(w[6])))
            else:
                op = w[1]
                a = w[2] if len(w) > 2 else None
                b = w[3] if len(w) > 3 else None
                if op in ("jmp", "call"):
                    a = int(a)
                if op in ("set", "jnz"):
                    b = int(b)
                self.code.append((op, a, b))
        n = len(self.code)

        # Function of every address.
        self.fn_of = [0] * n
        for f, (lo, hi) in enumerate(zip(self.fn_lo, self.fn_hi)):
            for a in range(lo, hi + 1):
                self.fn_of[a] = f

        # Row of every address (rule 3): the last row at or before the address inside the
        # same function; None in a function without rows. row_start marks row beginnings.
        self.row_line = [None] * n
        self.row_stmt = [False] * n
        self.row_first = [None] * n
        self.row_start = [False] * n
        by_addr = {r[0]: r for r in rows}
        for f in range(len(self.fn_name)):
            cur = None
            for a in range(self.fn_lo[f], self.fn_hi[f] + 1):
                if a in by_addr:
                    cur = by_addr[a]
                    self.row_start[a] = True
                if cur is not None:
                    self.row_first[a] = cur[0]
                    self.row_line[a] = cur[1]
                    self.row_stmt[a] = cur[2]
        self.stmt_rows = [r for r in rows if r[2]]

        # Inline instances (rule 4). A scope is ("f", function index) or ("i", instance id).
        self.inl_fn = {}
        self.inl_up = {}
        self.inl_call = {}
        self.inl_lo = {}
        self.inl_hi = {}
        for iid, fname, up, call, lo, hi in inls:
            self.inl_fn[iid] = fname
            self.inl_up[iid] = ("i", int(up)) if up.isdigit() else ("f", self.fn_name.index(up))
            self.inl_call[iid] = call
            self.inl_lo[iid] = lo
            self.inl_hi[iid] = hi
        # Instances holding each address, outermost first (they nest, siblings are disjoint).
        self.holding = [[] for _ in range(n)]
        for iid in sorted(self.inl_fn, key=lambda i: (self.inl_lo[i], -self.inl_hi[i], i)):
            for a in range(self.inl_lo[iid], self.inl_hi[iid] + 1):
                self.holding[a].append(iid)
        for a in range(n):
            self.holding[a].sort(key=lambda i: self._nest(i))

    def _nest(self, iid):
        d = 0
        up = self.inl_up[iid]
        while up[0] == "i":
            d += 1
            up = self.inl_up[up[1]]
        return d

    def chain(self, addr):
        """Rule 7: the function, then every instance holding the address, outermost first."""
        return [("f", self.fn_of[addr])] + [("i", i) for i in self.holding[addr]]

    def name(self, scope):
        return self.fn_name[scope[1]] if scope[0] == "f" else self.inl_fn[scope[1]]

    def holds(self, scope, addr):
        if scope[0] == "f":
            return self.fn_lo[scope[1]] <= addr <= self.fn_hi[scope[1]]
        return self.inl_lo[scope[1]] <= addr <= self.inl_hi[scope[1]]

    def parent(self, scope):
        return self.inl_up[scope[1]]

    def line(self, addr):
        v = self.row_line[addr]
        return 0 if v is None else v

    def starting(self, addr):
        """Instances that begin exactly at addr, outermost first."""
        return [i for i in self.holding[addr] if self.inl_lo[i] == addr]


class Stop(Exception):
    """Raised inside a command to end it with a stop kind ('hit', 'step', 'done')."""

    def __init__(self, kind):
        self.kind = kind


class Ended(Exception):
    """Raised when the program ends during a command."""


class Session:
    def __init__(self, prog, tape):
        self.p = prog
        self.tape = tape
        self.at = 0
        self.pc = prog.fn_lo[0]
        self.regs = [0, 0, 0, 0]
        self.calls = []          # [(return address, caller registers)]
        self.hid = 0             # hidden innermost scopes of the innermost frame
        self.locs = set()        # every breakpoint location address
        self.nbreak = 0
        self.executed = 0        # instructions executed so far (the verifier's volume count)

    # ----- the machine -------------------------------------------------------------

    def depth(self):
        return len(self.calls)

    def exec1(self):
        """Execute one instruction. Raises Ended when the program ends."""
        self.executed += 1
        op, a, b = self.p.code[self.pc]
        r = "abcd".index(a) if op in ("set", "in", "dec", "jnz") else None
        if op == "nop":
            self.pc += 1
        elif op == "set":
            self.regs[r] = b
            self.pc += 1
        elif op == "in":
            self.regs[r] = self.tape[self.at] if self.at < len(self.tape) else 0
            self.at += 1
            self.pc += 1
        elif op == "dec":
            self.regs[r] -= 1
            self.pc += 1
        elif op == "jnz":
            self.pc = b if self.regs[r] else self.pc + 1
        elif op == "jmp":
            self.pc = a
        elif op == "call":
            self.calls.append((self.pc + 1, self.regs))
            self.regs = [0, 0, 0, 0]
            self.pc = a
        else:
            if not self.calls:
                raise Ended()
            self.pc, self.regs = self.calls.pop()

    def tick(self):
        """One instruction, then the breakpoint check every command shares (rule 8)."""
        self.exec1()
        if self.pc in self.locs:
            self.hid = 0
            raise Stop("hit")

    # ----- what a stop prints (rules 6 and 7) --------------------------------------

    def frames(self):
        p = self.p
        out = []
        looks = [(self.pc, self.hid)] + [(ret - 1, 0) for ret, _ in reversed(self.calls)]
        for addr, hidden in looks:
            ch = p.chain(addr)
            for k in range(len(ch) - 1 - hidden, -1, -1):
                shown = p.inl_call[ch[k + 1][1]] if k + 1 < len(ch) else p.line(addr)
                out.append("%s:%d" % (p.name(ch[k]), shown))
        return out

    # ----- breakpoints (rule 5) -----------------------------------------------------

    def do_break(self, line):
        p = self.p
        best = {}
        for addr, ln, _ in p.stmt_rows:
            if ln != line:
                continue
            scope = p.chain(addr)[-1]
            if scope not in best or addr < best[scope]:
                best[scope] = addr
        where = sorted(best.values())
        self.nbreak += 1
        self.locs.update(where)
        return " ".join(["b%d" % self.nbreak] + [str(a) for a in where])

    # ----- run control ---------------------------------------------------------------

    def do_run(self):
        if self.pc in self.locs:
            self.hid = 0
            raise Stop("hit")
        self.do_cont()

    def do_cont(self):
        # Rule 8: run to a hit or the end.
        while True:
            self.tick()

    def visible(self):
        """The innermost frame's scopes and how many of them are shown."""
        ch = self.p.chain(self.pc)
        return ch, len(ch) - self.hid

    def do_finish(self):
        # Rule 16.
        ch, vis = self.visible()
        scope = ch[vis - 1]
        d0 = self.depth()
        if scope[0] == "i":
            while True:
                self.tick()
                if self.depth() == d0 and not self.p.holds(scope, self.pc):
                    break
        else:
            while True:
                self.tick()
                if self.depth() < d0:
                    break
        self.hid = len(self.p.starting(self.pc))
        raise Stop("done")

    def do_step(self, into):
        p = self.p
        ch, vis = self.visible()
        scope = ch[vis - 1]
        line = p.inl_call[ch[vis][1]] if self.hid else p.line(self.pc)   # rule 9
        self.st = {"d": self.depth(), "scope": scope, "line": line, "into": into}
        if self.hid:
            outer_hidden = ch[vis]
            if into:
                self.hid -= 1                                        # rule 10: reveal
                raise Stop("step")
            # Rule 10: next over the outermost hidden instance, as rule 13 does.
            self.hid = 0
            self.over_instance(outer_hidden)
            self.arrive()
        while True:
            before = self.pc
            before_row = p.row_first[before]
            self.tick()
            d = self.depth()
            st = self.st
            if d > st["d"]:
                # Rule 11: a call from the stepping frame.
                callee = p.fn_of[self.pc]
                if into and p.fn_has_lines[callee]:
                    self.hid = len(p.starting(self.pc))
                    raise Stop("step")
                ret = self.calls[-1][0]
                while True:
                    self.tick()
                    if self.depth() == st["d"]:
                        break
                # The call counts as a move from the call instruction to the return address.
                if p.row_first[self.pc] != p.row_first[ret - 1]:
                    self.arrive()
            elif d < st["d"]:
                # Rule 15: the stepping frame returned.
                st["d"] = d
                entered = p.starting(self.pc)
                ch2 = p.chain(self.pc)
                st["scope"] = ch2[len(ch2) - 1 - len(entered)]
                self.arrive()
            elif p.row_first[self.pc] != before_row or p.fn_of[self.pc] != p.fn_of[before]:
                self.arrive()

    def over_instance(self, inst):
        """Run until execution leaves the instance in the stepping frame (rules 10, 13)."""
        d0 = self.st["d"]
        while True:
            self.tick()
            if self.depth() == d0 and not self.p.holds(inst, self.pc):
                return

    def arrive(self):
        """Judge an arrival at self.pc in the stepping frame (rules 12, 13, 14)."""
        p = self.p
        while True:
            st = self.st
            addr = self.pc
            # Rule 14: leaving the stepping scope.
            while st["scope"][0] == "i" and not p.holds(st["scope"], addr):
                st["scope"] = p.parent(st["scope"])
            # Rule 13: instances starting here, below the stepping scope.
            ch = p.chain(addr)
            k = ch.index(st["scope"])
            below = [s for s in ch[k + 1:] if p.inl_lo[s[1]] == addr]
            if below:
                first = below[0]
                if p.inl_call[first[1]] == st["line"]:
                    if st["into"]:
                        self.hid = len(below) - 1
                        raise Stop("step")
                    self.over_instance(first)
                    continue          # judge where it lands, with the same scope and line
                self.hid = len(below)
                raise Stop("step")
            # Rule 12.
            ln = p.row_line[addr]
            if ln is None:
                return
            if p.row_start[addr]:
                if p.row_stmt[addr] and ln != 0 and ln != st["line"]:
                    self.hid = 0
                    raise Stop("step")
                return
            if ln != 0:
                st["line"] = ln
            return


def play(image_text, tape, commands):
    prog = Program(image_text)
    s = Session(prog, tape)
    out = []
    over = False
    for raw in commands:
        w = raw.split()
        if not w:
            continue
        if w[0] == "break":
            out.append(s.do_break(int(w[1])))
            continue
        if over:
            out.append("exit")
            continue
        try:
            {"run": s.do_run, "cont": s.do_cont, "finish": s.do_finish,
             "step": lambda: s.do_step(True), "next": lambda: s.do_step(False)}[w[0]]()
        except Stop as e:
            out.append(" ".join([e.kind, str(s.pc)] + s.frames()))
        except Ended:
            over = True
            out.append("exit")
    return out
