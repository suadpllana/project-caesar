"""Session generator: programs, tapes and scripts, shaped around the stop rules.

A program is generated at source level - functions made of statements - and compiled
into the image format the debugger reads: one instruction per address, line-table rows,
and inline instances for calls the "compiler" chose to inline. The compiler shapes rows
the way optimizing compilers do, because each shape exercises one rule:

  split row       a line with two statement rows            -> same-line row starts (rule 12)
  ns row          a row that is not a statement             -> rule 12
  hoisted row     a non-statement row of the NEXT line       -> rule 12, adoption fence
  line-0 prefix   compiler code with no line                -> rule 12
  loop shape B/D  a back edge into the middle of a row      -> adoption (rule 12)
  call last       a call ending its row                     -> caller frames at pc-1 (rule 7)
  inline, no pre  an instance starting where its line does  -> call-site stops (rule 13)
  inline, pre     call-site code before the instance        -> step-into by call line (13)
  back-to-back    an instance ending where another begins   -> rules 13, 14, 16
  tail call       an inlined body ending in a call          -> pc-1 inside, return outside
  ccall           a tape-guarded call, used for recursion   -> frame checks (rules 11, 15)
  rowless         a function with no lines                  -> rule 11

Every image is checked against the guarantees the brief states (check_image) before it
is used. The tape is produced by simulating the program and choosing each value an `in`
reads from a policy keyed by what that `in` guards. Scripts are produced by driving the
sealed model one command at a time, so every command is issued from a real state.
"""

import random

import model

REGS = "abcd"


# ----------------------------------------------------------------------------------------
# Source level
# ----------------------------------------------------------------------------------------

class Stmt:
    def __init__(self, kind, **kw):
        self.kind = kind
        self.line = None
        self.kw = kw
        self.body = kw.get("body", [])

    def __getitem__(self, k):
        return self.kw.get(k)


class Func:
    def __init__(self, name, lines=True, inlinable=False):
        self.name = name
        self.lines = lines
        self.inlinable = inlinable
        self.body = []
        self.lo_line = None
        self.hi_line = None


def number_lines(funcs, rng):
    """Give every statement of every function a line, functions in disjoint blocks."""
    nxt = 1
    for f in funcs:
        if not f.lines:
            continue
        f.lo_line = nxt

        def walk(stmts):
            nonlocal nxt
            for s in stmts:
                nxt += 1 if rng.random() < 0.8 else 2
                s.line = nxt
                walk(s.body)
        walk(f.body)
        nxt += 1
        f.hi_line = nxt
        nxt += rng.choice((2, 3, 5))


# ----------------------------------------------------------------------------------------
# Compiler
# ----------------------------------------------------------------------------------------

class Compiler:
    def __init__(self, funcs, rng):
        self.funcs = {f.name: f for f in funcs}
        self.order = funcs
        self.rng = rng
        self.code = []
        self.rows = {}
        self.inls = []
        self.next_inl = 1
        self.fn_lo = {}
        self.fn_hi = {}
        self.fixups = []
        self.in_kind = {}          # address of every `in` -> what it guards

    def here(self):
        return len(self.code)

    def emit(self, *ins):
        self.code.append(list(ins))
        return len(self.code) - 1

    def row(self, line, stmt=True):
        a = self.here()
        assert a not in self.rows, "two rows at one address"
        self.rows[a] = (line, stmt)

    def filler(self, scratch):
        if self.rng.random() < 0.5:
            self.emit("nop")
        else:
            self.emit("set", scratch, self.rng.randint(0, 9))

    def compile(self):
        for f in self.order:
            self.fn_lo[f.name] = self.here()
            alloc = list(REGS)
            self.block(f, f.body, f.name if f.lines else None, alloc, inlined=False, scope=f.name)
            self.fn_hi[f.name] = self.here() - 1
        for idx, slot, target in self.fixups:
            self.code[idx][slot] = self.fn_lo[target] if isinstance(target, str) else target

    # A block is a list of statements compiled in one scope. `lines` is the owner function
    # name when rows are written, None for a rowless function.
    def block(self, f, stmts, lines, alloc, inlined, scope):
        for i, s in enumerate(stmts):
            nxt = stmts[i + 1] if i + 1 < len(stmts) else None
            last = nxt is None
            self.stmt(f, s, nxt, lines, alloc, inlined, scope, last)

    def mark(self, s, lines, stmt=True, line=None):
        if lines is not None:
            self.row(s.line if line is None else line, stmt)

    def take(self, alloc):
        assert len(alloc) > 1, "out of registers"
        return alloc.pop(0)

    def stmt(self, f, s, nxt, lines, alloc, inlined, scope, last):
        scratch = alloc[-1]
        k = s.kind
        if s["zero"] and lines is not None:
            self.row(0)
            for _ in range(s["zero"]):
                self.filler(scratch)
        if k == "plain":
            self.mark(s, lines)
            n = s["n"]
            for j in range(n):
                self.filler(scratch)
                if j == 0 and n > 1 and lines is not None:
                    if s["split"]:
                        self.row(s.line, True)
                    elif s["nsmid"]:
                        self.row(s.line, False)
                    elif s["hoist"] and nxt is not None and nxt.line is not None:
                        self.row(nxt.line, False)
                        self.filler(scratch)
                        self.row(s.line, False)
                    elif s["hoisttail"] and nxt is not None and nxt.line is not None:
                        self.row(nxt.line, False)
        elif k == "call":
            shape = s["shape"]
            self.mark(s, lines)
            if s["pre"] or shape == "hoistcall":
                self.filler(scratch)
            if shape == "hoistcall" and lines is not None and nxt is not None and nxt.line is not None:
                self.row(nxt.line, False)
            idx = self.emit("call", None)
            self.fixups.append((idx, 1, s["target"]))
            if shape == "mid":
                self.filler(scratch)
            elif shape == "split":
                self.mark(s, lines, True)
                self.filler(scratch)
            elif shape == "splitns":
                self.mark(s, lines, False)
                self.filler(scratch)
            elif shape == "hoistcall":
                self.filler(scratch)
            # shape "last": the call ends the row; the next statement starts at the return
        elif k == "ccall":
            self.mark(s, lines)
            r = scratch
            a_in = self.emit("in", r)
            self.in_kind[a_in] = ("ccall", s["target"])
            j1 = self.emit("jnz", r, None)
            j2 = self.emit("jmp", None)
            self.code[j1][2] = self.here()
            idx = self.emit("call", None)
            self.fixups.append((idx, 1, s["target"]))
            if s["tail"]:
                self.filler(scratch)
            self.code[j2][1] = self.here()
        elif k == "if":
            self.mark(s, lines)
            r = scratch
            a_in = self.emit("in", r)
            self.in_kind[a_in] = ("if",)
            j1 = self.emit("jnz", r, None)
            j2 = self.emit("jmp", None)
            self.code[j1][2] = self.here()
            self.block(f, s.body, lines, alloc, inlined, scope)
            self.code[j2][1] = self.here()
        elif k == "loop":
            self.loop(f, s, lines, alloc, inlined, scope)
        elif k == "inl":
            self.inline(f, s, lines, alloc, scope)
        elif k == "ret":
            if inlined:
                if s["empty"]:
                    return
                self.mark(s, lines)
                self.filler(scratch)
            else:
                self.mark(s, lines)
                if s["epi"] and lines is not None:
                    self.filler(scratch)
                    self.row(0)
                self.emit("ret")
        else:
            raise ValueError(k)

    def loop(self, f, s, lines, alloc, inlined, scope):
        shape = s["shape"]
        r = self.take(alloc)
        heavy = s["heavy"]
        if shape == "C":
            self.mark(s, lines)
            a_in = self.emit("in", r)
            self.in_kind[a_in] = ("loop", heavy, 1)
            top = self.here()
            if s["pad"]:
                self.emit("nop")
            self.emit("dec", r)
            self.emit("jnz", r, top)
        elif shape == "A":
            self.mark(s, lines)
            a_in = self.emit("in", r)
            self.in_kind[a_in] = ("loop", heavy, 1)
            top = self.here()
            self.block(f, s.body, lines, alloc, False, scope)
            self.mark(s, lines, True)
            self.emit("dec", r)
            self.emit("jnz", r, top)
        elif shape == "B":
            self.mark(s, lines)
            a_in = self.emit("in", r)
            self.in_kind[a_in] = ("loop", heavy, 1)
            top = self.here()
            self.emit("nop")
            self.block(f, s.body, lines, alloc, False, scope)
            if s["own"]:
                self.mark(s, lines, s["own"] == "stmt")
            self.emit("dec", r)
            self.emit("jnz", r, top)
        elif shape == "D":
            self.mark(s, lines)
            a_in = self.emit("in", r)
            self.in_kind[a_in] = ("loop", heavy, 0)
            test = self.here()
            j1 = self.emit("jnz", r, None)
            j2 = self.emit("jmp", None)
            self.code[j1][2] = self.here()
            self.block(f, s.body, lines, alloc, False, scope)
            self.emit("dec", r)
            self.emit("jmp", test)
            self.code[j2][1] = self.here()
        else:
            raise ValueError(shape)
        alloc.insert(0, r)

    def inline(self, f, s, lines, alloc, scope):
        target = self.funcs[s["target"]]
        assert target.inlinable and target.lines and lines is not None
        if s["pre"]:
            self.mark(s, lines)
            for _ in range(s["pre"]):
                self.filler(alloc[-1])
        iid = self.next_inl
        self.next_inl += 1
        lo = self.here()
        entry = len(self.inls)
        self.inls.append(None)
        self.block(target, target.body, target.name, alloc, True, iid)
        hi = self.here() - 1
        assert hi >= lo
        self.inls[entry] = (iid, target.name, scope, s.line, lo, hi)
        if s["post"] == "stmt":
            self.mark(s, lines, True)
            self.filler(alloc[-1])
        elif s["post"] == "ns":
            self.mark(s, lines, False)
            self.filler(alloc[-1])

    def image(self):
        out = []
        for f in self.order:
            if f.lines:
                out.append("fn %s %d %d %d %d" % (f.name, self.fn_lo[f.name], self.fn_hi[f.name],
                                                  f.lo_line, f.hi_line))
            else:
                out.append("fn %s %d %d" % (f.name, self.fn_lo[f.name], self.fn_hi[f.name]))
        for a, ins in enumerate(self.code):
            out.append(" ".join([str(a)] + [str(x) for x in ins]))
        for a in sorted(self.rows):
            line, stmt = self.rows[a]
            out.append("row %d %d" % (a, line) + ("" if stmt else " x"))
        for iid, fname, scope, call, lo, hi in self.inls:
            out.append("inl %d %s %s %d %d %d" % (iid, fname, scope, call, lo, hi))
        return "\n".join(out) + "\n"


# ----------------------------------------------------------------------------------------
# The guarantees the brief states, checked on every image
# ----------------------------------------------------------------------------------------

def check_image(text):
    p = model.Program(text)
    n = len(p.code)
    assert p.fn_lo[0] == 0
    for f in range(len(p.fn_name)):
        if f:
            assert p.fn_lo[f] == p.fn_hi[f - 1] + 1
        if p.fn_has_lines[f]:
            lo = p.fn_lo[f]
            assert p.row_start[lo] and p.row_stmt[lo] and p.row_line[lo], "function entry row"
        else:
            assert all(p.row_line[a] is None for a in range(p.fn_lo[f], p.fn_hi[f] + 1))
        last = p.code[p.fn_hi[f]][0]
        assert last in ("ret", "jmp"), "a function must not fall off its end"
    assert p.fn_hi[-1] == n - 1
    names = p.fn_name
    owner = {}
    for w in text.splitlines():
        t = w.split()
        if t and t[0] == "fn" and len(t) > 4:
            for ln in range(int(t[4]), int(t[5]) + 1):
                assert ln not in owner, "line shared between functions"
                owner[ln] = t[1]
    for a in range(n):
        op, x, y = p.code[a]
        if op == "call":
            assert x in p.fn_lo, "call target is not a function"
        if op in ("jmp", "jnz"):
            t = x if op == "jmp" else y
            assert p.fn_of[t] == p.fn_of[a], "jump leaves its function"
        if p.row_start[a]:
            ln = p.row_line[a]
            inner = p.chain(a)[-1]
            if ln:
                assert owner[ln] == p.name(inner), "row line not owned by the innermost scope"
    for iid in p.inl_fn:
        lo, hi = p.inl_lo[iid], p.inl_hi[iid]
        up = p.inl_up[iid]
        assert p.holds(up, lo) and p.holds(up, hi)
        assert p.row_start[lo] and p.row_stmt[lo] and p.row_line[lo], "instance entry row"
        assert hi + 1 <= p.fn_hi[p.fn_of[lo]] and p.row_start[hi + 1], "instance exit row"
        for a in range(lo, hi + 1):
            op, x, y = p.code[a]
            assert op != "ret", "ret inside an instance"
            if op in ("jmp", "jnz"):
                t = x if op == "jmp" else y
                assert lo <= t <= hi, "jump out of an instance"
        for a in range(n):
            if lo <= a <= hi:
                continue
            op, x, y = p.code[a]
            if op in ("jmp", "jnz"):
                t = x if op == "jmp" else y
                assert not (lo < t <= hi), "jump into the middle of an instance"
        if lo > 0 and p.fn_of[lo - 1] == p.fn_of[lo]:
            assert not (p.inl_lo[iid] < lo), "sanity"
    for iid in p.inl_fn:
        for jid in p.inl_fn:
            if iid < jid and p.inl_up[iid] == p.inl_up[jid]:
                a0, a1 = p.inl_lo[iid], p.inl_hi[iid]
                b0, b1 = p.inl_lo[jid], p.inl_hi[jid]
                assert a1 < b0 or b1 < a0, "siblings overlap"
    return p


# ----------------------------------------------------------------------------------------
# Tapes: simulate, choosing each value from a policy
# ----------------------------------------------------------------------------------------

def make_tape(comp, rng, heavy_range=None, max_depth=5, budget=40000):
    """Run the program once, choosing what every `in` reads; returns the tape.

    Loop counts are small unless the loop is marked heavy; conditional calls recurse
    with a probability that falls with call depth and stops at max_depth.
    """
    code = [tuple(c) for c in comp.code]
    pc = 0
    regs = [0, 0, 0, 0]
    calls = []
    tape = []
    steps = 0
    while True:
        steps += 1
        if steps > budget:
            return None
        op = code[pc][0]
        if op == "in":
            kind = comp.in_kind[pc]
            if kind[0] == "loop":
                if kind[1] and heavy_range:
                    v = rng.randint(*heavy_range)
                else:
                    v = rng.randint(kind[2], 3)
            elif kind[0] == "if":
                v = rng.randint(0, 1)
            else:
                depth = len(calls)
                v = 1 if depth < max_depth and rng.random() < 0.65 - 0.1 * depth else 0
            tape.append(v)
            regs[REGS.index(code[pc][1])] = v
            pc += 1
        elif op == "nop":
            pc += 1
        elif op == "set":
            regs[REGS.index(code[pc][1])] = code[pc][2]
            pc += 1
        elif op == "dec":
            regs[REGS.index(code[pc][1])] -= 1
            pc += 1
        elif op == "jnz":
            pc = code[pc][2] if regs[REGS.index(code[pc][1])] else pc + 1
        elif op == "jmp":
            pc = code[pc][1]
        elif op == "call":
            if len(calls) > 60:
                return None
            calls.append((pc + 1, regs))
            regs = [0, 0, 0, 0]
            pc = code[pc][1]
        else:
            if not calls:
                return tape
            pc, regs = calls.pop()


# ----------------------------------------------------------------------------------------
# Programs
# ----------------------------------------------------------------------------------------

class Shaper:
    """Random source programs. `knobs` weights the shapes for one family."""

    def __init__(self, rng, knobs):
        self.rng = rng
        self.k = knobs

    def p(self, key):
        return self.rng.random() < self.k.get(key, 0.0)

    def extras(self, s, allow_zero=True):
        if allow_zero and self.p("zero"):
            s.kw["zero"] = self.rng.randint(1, 2)
        return s

    def plain(self):
        s = Stmt("plain", n=self.rng.randint(1, 3))
        if s["n"] > 1:
            r = self.rng.random()
            if r < self.k.get("split", 0):
                s.kw["split"] = True
            elif r < self.k.get("split", 0) + self.k.get("nsmid", 0):
                s.kw["nsmid"] = True
            elif r < self.k.get("split", 0) + self.k.get("nsmid", 0) + self.k.get("hoist", 0):
                s.kw["hoist"] = True
            elif r < (self.k.get("split", 0) + self.k.get("nsmid", 0) + self.k.get("hoist", 0)
                      + self.k.get("hoisttail", 0)):
                s.kw["hoisttail"] = True
        return s

    def program(self):
        rng = self.rng
        k = self.k
        n_help = rng.randint(k.get("min_help", 1), k.get("max_help", 4))
        helpers = []
        leafs = []
        for i in range(n_help):
            lines = not self.p("rowless")
            f = Func("f%d" % i if lines else "g%d" % i, lines=lines,
                     inlinable=lines and self.p("inlinable"))
            helpers.append(f)
        main = Func("main")
        funcs = [main] + helpers
        # Callable targets for each function: later helpers only (keeps the static call
        # graph acyclic except for tape-guarded recursion, which may point anywhere).
        for idx, f in enumerate(funcs):
            later = [g for g in funcs[idx + 1:]]
            inl_targets = [g for g in later if g.inlinable]
            f.body = self.body(f, later, inl_targets, funcs, depth=0,
                               n=rng.randint(k.get("min_len", 3), k.get("max_len", 6)),
                               first=True)
            ret = Stmt("ret", empty=self.p("tailret"), epi=self.p("epi"))
            f.body.append(ret)
            if f.inlinable:
                last = f.body[-2] if len(f.body) > 1 else None
                if last is not None and last.kind in ("if", "ccall", "loop"):
                    ret.kw["empty"] = False
                if last is not None and last.kind == "inl":
                    ret.kw["empty"] = False
        return funcs

    def body(self, f, later, inl_targets, funcs, depth, n, first):
        rng = self.rng
        out = []
        for i in range(n):
            if (first and i == 0 and f.lines and not f.inlinable and f.name != "main"
                    and rng.random() < self.k.get("entryrec", 0.0)):
                out.append(Stmt("ccall", target=f.name, tail=rng.random() < 0.5))
                continue
            if first and i == 0 and inl_targets and f.lines and rng.random() < self.k.get("entryinl", 0.0):
                out.append(Stmt("inl", target=rng.choice(inl_targets).name, pre=0,
                                post=rng.choice(("none", "stmt", "ns"))))
                continue
            choice = rng.random()
            acc = 0.0
            s = None
            for kind, w in self.k["mix"]:
                acc += w
                if choice < acc:
                    s = self.make(kind, f, later, inl_targets, funcs, depth, first and i == 0)
                    break
            if s is None:
                s = self.plain()
            if not (first and i == 0):
                self.extras(s)
            out.append(s)
        return out

    def make(self, kind, f, later, inl_targets, funcs, depth, is_first):
        rng = self.rng
        k = self.k
        if kind == "plain":
            return self.plain()
        if kind == "call":
            targets = later
            if not targets:
                return self.plain()
            return Stmt("call", target=rng.choice(targets).name,
                        shape=rng.choice(k.get("call_shapes", ("mid", "last", "split", "splitns"))),
                        pre=rng.random() < 0.5)
        if kind == "ccall":
            pool = [g for g in funcs[1:] if not g.inlinable]
            if f.inlinable:
                pool = [g for g in pool if g is not f]
            if not pool:
                return self.plain()
            tgt = f if (not f.inlinable and rng.random() < k.get("selfrec", 0.5)) else rng.choice(pool)
            return Stmt("ccall", target=tgt.name, tail=rng.random() < 0.5)
        if kind == "inl":
            if not f.lines or not inl_targets or depth > 2:
                return self.plain()
            t = rng.choice(inl_targets)
            return Stmt("inl", target=t.name, pre=0 if rng.random() < k.get("nopre", 0.5) else rng.randint(1, 2),
                        post=rng.choice(("none", "none", "stmt", "ns")))
        if kind == "if":
            if depth > 2:
                return self.plain()
            return Stmt("if", body=self.body(f, later, inl_targets, funcs, depth + 1,
                                             n=rng.randint(1, 2), first=False))
        if kind == "loop":
            if depth > 1:
                return self.plain()
            shape = rng.choice(k.get("loop_shapes", ("A", "B", "C", "D")))
            heavy = rng.random() < k.get("heavy", 0.0)
            if shape == "C":
                return Stmt("loop", shape="C", heavy=heavy, pad=rng.random() < 0.5)
            body = self.body(f, later, inl_targets, funcs, depth + 1,
                             n=rng.randint(1, 2), first=False)
            own = rng.choice((None, "stmt", "ns")) if shape == "B" else None
            return Stmt("loop", shape=shape, heavy=heavy and shape != "D", body=body, own=own)
        raise ValueError(kind)


def fix_inline_rets(funcs):
    """An inlined body that ends in an if, ccall, loop or nested inline keeps its ret row."""
    for f in funcs:
        if not f.inlinable:
            continue
        ret = f.body[-1]
        prev = f.body[-2] if len(f.body) > 1 else None
        if prev is None or prev.kind in ("if", "ccall", "loop", "inl"):
            ret.kw["empty"] = False
        if prev is not None and prev.kind == "call" and prev["shape"] == "last":
            pass


MAX_ADDRESSES = 400      # the brief states it: no graded program is longer


def build(rng, knobs, heavy_range=None, max_depth=5, budget=40000, tries=400):
    """One program, compiled and checked, with a tape that makes it end."""
    for _ in range(tries):
        funcs = Shaper(rng, knobs).program()
        fix_inline_rets(funcs)
        number_lines(funcs, rng)
        comp = Compiler(funcs, rng)
        try:
            comp.compile()
        except AssertionError:
            continue
        if len(comp.code) > MAX_ADDRESSES:
            continue
        text = comp.image()
        try:
            check_image(text)
        except AssertionError:
            continue
        tape = make_tape(comp, rng, heavy_range=heavy_range, max_depth=max_depth, budget=budget)
        if tape is None:
            continue
        return text, tape, comp
    raise RuntimeError("could not build a program for %r" % (knobs,))


# ----------------------------------------------------------------------------------------
# Scripts, driven through the model
# ----------------------------------------------------------------------------------------

def interesting_lines(prog):
    """Lines with statement rows, weighted towards inlined code and deep scopes."""
    lines = {}
    for addr, ln, _ in prog.stmt_rows:
        if not ln:
            continue
        w = 1 + 2 * len(prog.holding[addr])
        lines[ln] = max(lines.get(ln, 0), w)
    return lines


def script(text, tape, rng, n_cmds=(8, 22), weights=None, n_breaks=(1, 3), count=False,
           hot=()):
    """Issue commands against the model until the program ends or the budget is spent.

    `hot` lines are where a heavy loop sits in one row: they get breakpoints, and a stop on
    one is followed by step or next, so the loop is crossed inside the stepping frame.
    With count=True, also return how many instructions ran in the stepping frame of a step
    or next (the volume an engine that single-steps its own frame would pay for).
    """
    prog = model.Program(text)
    s = model.Session(prog, tape)
    lines = interesting_lines(prog)
    pool = sorted(lines)
    wts = [lines[x] for x in pool]
    cmds = []
    out = []
    in_frame = [0]
    ctx = [None]
    plain_exec = s.exec1

    def exec1():
        if ctx[0] in ("step", "next") and hasattr(s, "st") and s.depth() == s.st["d"]:
            in_frame[0] += 1
        plain_exec()
    s.exec1 = exec1

    def add_break(ln=None):
        if ln is None:
            ln = rng.choices(pool, weights=wts)[0]
        cmds.append("break %d" % ln)
        out.append(s.do_break(ln))

    hot = sorted(set(hot) & set(pool))
    for _ in range(rng.randint(*n_breaks)):
        add_break()
    for ln in rng.sample(hot, min(len(hot), 2)):
        add_break(ln)
    weights = weights or {"step": 35, "next": 30, "finish": 14, "cont": 12, "break": 9}
    total = rng.randint(*n_cmds)
    first = True
    while len(cmds) < total:
        if first:
            kind = "run"
            first = False
        elif hot and s.frames() and int(s.frames()[0].split(":")[1]) in hot and rng.random() < 0.85:
            kind = rng.choice(("next", "next", "step"))
        else:
            kind = rng.choices(list(weights), weights=list(weights.values()))[0]
        ctx[0] = kind
        if kind == "break":
            add_break()
            continue
        if kind == "finish":
            ch, vis = s.visible()
            if not s.calls and ch[vis - 1][0] == "f":
                continue
        cmds.append(kind)
        try:
            {"run": s.do_run, "cont": s.do_cont, "finish": s.do_finish,
             "step": lambda: s.do_step(True), "next": lambda: s.do_step(False)}[kind]()
        except model.Stop as e:
            out.append(" ".join([e.kind, str(s.pc)] + s.frames()))
        except model.Ended:
            out.append("exit")
            break
    if count:
        return cmds, out, s.executed, in_frame[0]
    return cmds, out


# ----------------------------------------------------------------------------------------
# Families
# ----------------------------------------------------------------------------------------

BASE_MIX = [("plain", 0.30), ("call", 0.18), ("ccall", 0.10), ("inl", 0.20), ("if", 0.07), ("loop", 0.15)]

FAMILIES = {
    # Ordinary code: no inlining, no special rows. The fence against overshooting.
    "plain": dict(mix=[("plain", 0.45), ("call", 0.30), ("if", 0.1), ("loop", 0.15)],
                  inlinable=0.0, rowless=0.0, loop_shapes=("A", "C"),
                  call_shapes=("mid", "last", "split")),
    # Inlining in every form, nested and back to back.
    "inline": dict(mix=[("plain", 0.25), ("call", 0.12), ("inl", 0.45), ("loop", 0.08), ("if", 0.1)],
                   inlinable=0.85, rowless=0.05, nopre=0.55, tailret=0.4, min_help=2, max_help=4),
    # Row shapes: split, non-statement, hoisted, line-0, back edges into rows.
    "rows": dict(mix=[("plain", 0.40), ("call", 0.15), ("loop", 0.30), ("inl", 0.1), ("if", 0.05)],
                 inlinable=0.5, rowless=0.05, split=0.3, nsmid=0.25, hoist=0.3, zero=0.2, epi=0.4,
                 loop_shapes=("B", "D", "B", "A")),
    # Recursion through tape-guarded calls, including from inlined code.
    "rec": dict(mix=[("plain", 0.25), ("ccall", 0.35), ("call", 0.1), ("inl", 0.2), ("loop", 0.1)],
                inlinable=0.5, rowless=0.1, selfrec=0.7, tailret=0.5),
    # Functions without lines, stepped into and finished into.
    "rowless": dict(mix=[("plain", 0.3), ("call", 0.35), ("ccall", 0.1), ("inl", 0.15), ("loop", 0.1)],
                    inlinable=0.4, rowless=0.45, min_help=2),
    # Everything at once.
    "mixed": dict(mix=BASE_MIX, inlinable=0.5, rowless=0.15, split=0.15, nsmid=0.1, hoist=0.15,
                  zero=0.1, epi=0.2, nopre=0.5, tailret=0.3, selfrec=0.5),
}


# Long loops, crossed by single commands: one-line loops in the stepping frame, loops in
# called functions, in inlined instances and in functions without lines. These sessions
# carry the stated limit: an engine that single-steps any of them cannot finish.
HEAVY = dict(mix=[("plain", 0.25), ("call", 0.22), ("ccall", 0.05), ("inl", 0.2), ("loop", 0.28)],
             inlinable=0.5, rowless=0.25, heavy=0.7, loop_shapes=("C", "C", "C", "A", "B"),
             nopre=0.5, tailret=0.3, selfrec=0.3, min_help=2, max_help=4)


def heavy_lines(funcs):
    """Lines of heavy one-line loops, wherever their function's body is compiled."""
    out = set()

    def walk(stmts):
        for st in stmts:
            if st.kind == "loop" and st["heavy"] and st["shape"] == "C":
                out.add(st.line)
            walk(st.body)
    for f in funcs:
        if f.lines:
            walk(f.body)
    return out


def heavy_session(rng, heavy_range=(150000, 350000), floor=1500000, tries=60):
    """A heavy session that crosses at least `floor` instructions inside a stepping frame."""
    for _ in range(tries):
        text, tape, comp = build(rng, HEAVY, heavy_range=heavy_range, budget=60000000)
        hot = heavy_lines(comp.order)
        if not hot or len(tape) > 20000:
            continue
        cmds, out, done, in_frame = script(text, tape, rng, n_cmds=(10, 24), count=True, hot=hot)
        if in_frame >= floor:
            return {"family": "heavy", "image": text, "tape": tape, "cmds": cmds,
                    "want": out, "volume": done, "in_frame": in_frame}
    raise RuntimeError("no heavy session reached the floor")


FAMILIES.update({
    # Nested instances that start together, functions that begin with an inlined call, calls
    # that end their row just before an inlined call: where hidden depth is decided.
    "nest": dict(mix=[("plain", 0.2), ("call", 0.25), ("inl", 0.45), ("loop", 0.05), ("if", 0.05)],
                 inlinable=0.9, rowless=0.05, nopre=0.8, entryinl=0.7, tailret=0.5, min_help=3,
                 max_help=5, call_shapes=("last", "last", "mid", "split")),
    # Self-recursion stepped with next and finish, where a planted return address fires in a
    # deeper frame first.
    "recur": dict(mix=[("plain", 0.25), ("ccall", 0.45), ("inl", 0.15), ("call", 0.1), ("loop", 0.05)],
                  inlinable=0.4, rowless=0.05, selfrec=0.95, entryrec=0.5, tailret=0.5, min_help=1,
                  max_help=3),
    # Non-statement rows of the next line, some holding a call.
    "hoist": dict(mix=[("plain", 0.45), ("call", 0.35), ("loop", 0.1), ("inl", 0.1)],
                  inlinable=0.4, rowless=0.05, hoist=0.2, hoisttail=0.35, nsmid=0.1, split=0.1,
                  call_shapes=("hoistcall", "hoistcall", "split", "last", "mid")),
})

WEIGHTS = {
    "recur": {"step": 25, "next": 35, "finish": 25, "cont": 10, "break": 5},
    "nest": {"step": 45, "next": 30, "finish": 15, "cont": 5, "break": 5},
}


def session(family, rng, **kw):
    knobs = FAMILIES[family]
    text, tape, _ = build(rng, knobs, budget=kw.get("budget", 40000))
    cmds, out = script(text, tape, rng, weights=WEIGHTS.get(family))
    return {"family": family, "image": text, "tape": tape, "cmds": cmds, "want": out}
