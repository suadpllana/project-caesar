"""Sealed model of the runtime. Root-only; never visible to the run.

This is a second implementation of the whole thing, written from the specification rather
than from the tree, and it shares no code with the tree - not the parser, not the fiber
representation, not the unwinding. The tree walks a flat op list with a jump table and an
explicit pending-exception slot; this parses the same text into a nested statement tree
and runs each fiber as a Python generator, so cuts really are exceptions thrown into a
suspended frame and cleanup blocks really do run after their guard's frame has gone. Two
implementations that agree on every event of several hundred random programs agree about
the semantics and not about a shared bug.

What it produces, per program, is exactly what the verifier compares against: the ordered
event trace and the token list of every fiber.

The rules it implements, which are the rules the instruction states:

  delivery   At a checkpoint, scan the fiber's chain outward from the fiber and stop
             after the first guard carrying a shield; that guard is inside the window and
             everything enclosing it is out. Of the marked guards in the window the
             OUTERMOST is the one delivered, so that absorbing it does not leave the fiber
             running inside an enclosing guard that is also marked.

  rest       A cut comes to rest at a closing guard when that guard is marked and nothing
             still visible outside it is marked. Decided from the marks standing at the
             moment the guard closes, never from the guard chosen when the cut was raised.

  marks      Sticky. Nothing clears one; a guard stops mattering only when it closes.

  cleanup    Runs after its own guard has closed, in the guard that encloses it. A cut
             arriving inside a cleanup block abandons the rest of that block, and the
             newer of two in-flight exceptions is the one that keeps travelling.

  bands      A fiber cannot leave a band while a child is alive, whatever has reached it;
             it is asked again when the last child ends. A fiber unwinding into a band it
             owns marks the band's own guard first. At the close: a mark on a guard
             enclosing the band outranks everything the children collected and leaves
             alone; otherwise the collected payloads leave as a bundle ordered by when
             each child ended and then by the order the children were made; otherwise the
             band's own mark is what the close was for and nothing leaves.

  spawn      A child's inherited chain is the chain that stood when the band was opened,
             not the one its parent holds at the moment of the spawn.
"""

CAP = 200000
FLAT = ("S", "P", "W", "H", "M", "F", "N")


class Box(Exception):
    def __init__(self, kind, val):
        Exception.__init__(self, kind)
        self.kind = kind
        self.val = val


class Halt(Exception):
    pass


class G:
    def __init__(self, lbl, dl, sh, band):
        self.lbl = lbl
        self.dl = dl
        self.sh = sh
        self.hit = False
        self.cl = None
        self.band = band


class B:
    def __init__(self, lbl, own):
        self.gd = G(lbl, None, False, True)
        self.lbl = lbl
        self.own = own
        self.kids = []
        self.errs = []
        self.inh = []


class F:
    def __init__(self, fid, name):
        self.fid = fid
        self.name = name
        self.gen = None
        self.inh = []
        self.bl = []
        self.st = 0
        self.wake = None
        self.warm = False
        self.req = None
        self.hold = None
        self.toks = []
        self.home = None


def parse(text):
    out = {}
    name = None
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith(":"):
            if name is not None:
                out[name] = block(lines, 0)[0]
            name = s[1:].strip()
            lines = []
        else:
            lines.append(s.split())
    if name is not None:
        out[name] = block(lines, 0)[0]
    return out


def block(lines, i, stop=None):
    body = []
    while i < len(lines):
        tok = lines[i]
        k = tok[0]
        if stop is not None and k == stop:
            return body, i + 1
        if k == "G":
            inner, i = block(lines, i + 1, "E")
            body.append(("G", int(tok[1]), int(tok[2]), int(tok[3]), inner))
            continue
        if k == "B":
            inner, i = block(lines, i + 1, "X")
            body.append(("B", int(tok[1]), inner))
            continue
        if k == "A":
            inner, i = block(lines, i + 1, "Z")
            body.append(("A", inner))
            continue
        if k in ("E", "X", "Z"):
            raise ValueError(k)
        if k == "N":
            body.append(("N", tok[1]))
        elif k in ("P", "F"):
            body.append((k,))
        else:
            body.append((k, int(tok[1])))
        i += 1
    if stop is not None:
        raise ValueError(stop)
    return body, i


class Sim:
    def __init__(self, progs):
        self.pr = progs
        self.t = 0
        self.rq = []
        self.fs = []
        self.gm = {}
        self.tr = []
        self.n = 0

    def ev(self, *row):
        self.tr.append((self.t,) + row)

    # ---- the two decisions the tree hands to the submitted files ----

    def window(self, ch):
        out = []
        for g in reversed(ch):
            out.append(g)
            if g.sh:
                break
        return out

    def chain(self, f):
        out = list(f.inh)
        for e in f.bl:
            out.append(e if isinstance(e, G) else e.gd)
        return out

    def pick(self, f):
        best = None
        for g in self.window(self.chain(f)):
            if g.hit:
                best = g
        return best

    def rests(self, f, g):
        if not g.hit:
            return False
        for h in self.window(self.chain(f)):
            if h.hit:
                return False
        return True

    def leaves(self, f, bd, gg):
        if gg is not None and gg is not bd.gd:
            return ("cut", gg)
        if bd.errs:
            return ("bun", tuple(e[2] for e in
                                 sorted(bd.errs, key=lambda e: (e[0], e[1]))))
        return None

    # ---- fiber bodies ----

    def walk(self, f, body):
        for st in body:
            k = st[0]
            if k == "S":
                f.toks.append(st[1])
                self.ev("tk", f.fid, st[1])
            elif k == "P":
                yield ("cp",)
            elif k == "W":
                yield ("w", st[1])
            elif k == "M":
                g = self.gm.get(st[1])
                if g is not None:
                    self.mark(g, "op")
            elif k == "H":
                g = self.tip(f)
                if g is not None:
                    g.sh = bool(st[1])
            elif k == "A":
                g = self.tip(f)
                if g is not None:
                    g.cl = st[1]
            elif k == "F":
                raise Box("err", f.fid)
            elif k == "N":
                self.hatch(f, st[1])
            elif k == "G":
                yield from self.guard(f, st)
            elif k == "B":
                yield from self.band(f, st)

    def tip(self, f):
        if not f.bl:
            return None
        e = f.bl[-1]
        return e if isinstance(e, G) else e.gd

    def guard(self, f, st):
        g = G(st[1], None if st[2] < 0 else self.t + st[2], bool(st[3]), False)
        f.bl.append(g)
        self.gm[g.lbl] = g
        self.ev("op", f.fid, g.lbl)
        if g.dl is not None and g.dl <= self.t:
            self.mark(g, "dl")
        box = None
        try:
            yield from self.walk(f, st[4])
        except Box as b:
            box = b
        f.bl.pop()
        self.gm.pop(g.lbl, None)
        self.ev("cl", f.fid, g.lbl, "ok" if box is None else box.kind)
        if box is not None and box.kind == "cut" and self.rests(f, g):
            box = None
        cell = [box]
        yield from self.sweep(f, g, cell)
        if cell[0] is not None:
            raise cell[0]

    def sweep(self, f, g, cell):
        if not g.cl:
            return
        self.ev("cu", f.fid, g.lbl)
        try:
            yield from self.walk(f, g.cl)
        except Box as b:
            cell[0] = b

    def band(self, f, st):
        bd = B(st[1], f)
        f.bl.append(bd)
        self.gm[bd.lbl] = bd.gd
        bd.inh = self.chain(f)
        self.ev("bo", f.fid, bd.lbl)
        box = None
        try:
            yield from self.walk(f, st[2])
        except Box as b:
            box = b
        if box is None:
            while self.busy(bd):
                yield ("join", bd)
            gg = self.pick(f)
            f.bl.pop()
            self.gm.pop(bd.lbl, None)
            res = self.leaves(f, bd, gg)
            self.ev("bc", f.fid, bd.lbl, res[0] if res else "ok")
            if res is not None:
                if res[0] == "cut":
                    self.ev("ct", f.fid, res[1].lbl)
                    box = Box("cut", res[1])
                else:
                    box = Box("bun", res[1])
        else:
            while self.busy(bd):
                self.mark(bd.gd, "op")
                yield ("join", bd)
            f.bl.pop()
            self.gm.pop(bd.lbl, None)
            self.ev("bc", f.fid, bd.lbl, box.kind)
        cell = [box]
        yield from self.sweep(f, bd.gd, cell)
        if cell[0] is not None:
            raise cell[0]

    # ---- scheduler ----

    def busy(self, bd):
        return len([k for k in bd.kids if k.st != 2])

    def hatch(self, f, name):
        bd = None
        for e in reversed(f.bl):
            if isinstance(e, B):
                bd = e
                break
        if bd is None:
            return
        kid = self.birth(name, list(bd.inh), bd)
        bd.kids.append(kid)
        self.ev("sp", f.fid, kid.fid)
        self.rq.append(kid)

    def birth(self, name, inh, home):
        f = F(len(self.fs), name)
        f.inh = inh
        f.home = home
        f.gen = self.walk(f, self.pr[name])
        self.fs.append(f)
        self.ev("go", f.fid, name)
        return f

    def mark(self, g, why):
        if g.hit:
            return
        g.hit = True
        self.ev("mk", g.lbl, why)
        for f in self.fs:
            if f.st == 1 and f.wake is not None and self.pick(f) is not None:
                f.wake = None
                f.st = 0
                self.rq.append(f)

    def resume(self, f, throw=None):
        try:
            if throw is None:
                f.req = next(f.gen)
            else:
                f.req = f.gen.throw(throw)
        except Box as b:
            self.done(f, b)
            return False
        except StopIteration:
            self.done(f, None)
            return False
        return True

    def step(self, f):
        self.ev("on", f.fid)
        while True:
            self.n += 1
            if self.n > CAP:
                raise Halt("cap")
            if f.req is None:
                if not self.resume(f):
                    return
            req = f.req
            if req[0] == "cp":
                g = self.pick(f)
                f.req = None
                if g is not None:
                    self.ev("ct", f.fid, g.lbl)
                    if not self.resume(f, Box("cut", g)):
                        return
                    continue
                f.st = 1
                self.rq.append(f)
                return
            if req[0] == "w":
                if not f.warm:
                    g = self.pick(f)
                    if g is not None:
                        f.req = None
                        self.ev("ct", f.fid, g.lbl)
                        if not self.resume(f, Box("cut", g)):
                            return
                        continue
                    if req[1] <= 0:
                        f.req = None
                        f.st = 1
                        self.rq.append(f)
                        return
                    f.warm = True
                    f.wake = self.t + req[1]
                    f.st = 1
                    return
                f.warm = False
                f.wake = None
                g = self.pick(f)
                f.req = None
                if g is not None:
                    self.ev("ct", f.fid, g.lbl)
                    if not self.resume(f, Box("cut", g)):
                        return
                continue
            bd = req[1]
            if self.busy(bd):
                self.pick(f)
                f.st = 1
                f.hold = bd
                return
            f.req = None

    def done(self, f, box):
        f.st = 2
        if box is None:
            self.ev("en", f.fid, "ok", 0)
        elif box.kind == "cut":
            self.ev("en", f.fid, "cut", box.val.lbl)
        elif box.kind == "err":
            self.ev("en", f.fid, "err", box.val)
        else:
            self.ev("en", f.fid, "bun", list(box.val))
        bd = f.home
        if bd is None:
            return
        if box is not None and box.kind in ("err", "bun"):
            pay = [box.val] if box.kind == "err" else list(box.val)
            for p in pay:
                bd.errs.append((self.t, f.fid, p))
            self.mark(bd.gd, "op")
        if not self.busy(bd) and bd.own.hold is bd:
            bd.own.hold = None
            bd.own.st = 0
            self.rq.append(bd.own)

    def tick(self):
        cand = []
        for f in self.fs:
            if f.st == 1 and f.wake is not None:
                cand.append(f.wake)
        for g in self.gm.values():
            if g.dl is not None and not g.hit:
                cand.append(g.dl)
        if not cand:
            return False
        self.t = max(min(cand), self.t)
        for lbl in sorted(self.gm):
            g = self.gm.get(lbl)
            if g is not None and g.dl is not None and not g.hit and g.dl <= self.t:
                self.mark(g, "dl")
        for f in self.fs:
            if f.st == 1 and f.wake is not None and f.wake <= self.t:
                f.wake = None
                f.st = 0
                self.rq.append(f)
        return True

    def run(self, root):
        self.birth(root, [], None)
        self.rq.append(self.fs[0])
        while True:
            while self.rq:
                f = self.rq.pop(0)
                if f.st == 2:
                    continue
                f.st = 0
                self.step(f)
            if not self.tick():
                break
        return {
            "tr": [tuple(r) for r in self.tr],
            "tk": [(f.fid, f.name, tuple(f.toks)) for f in self.fs],
        }


def solve(text, root="main"):
    return Sim(parse(text)).run(root)
