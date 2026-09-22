#!/bin/bash
# cheat: slow-half
# exactly correct, plants return addresses but single-steps its own frame
set -euo pipefail
mkdir -p /app/dbg
cat > /app/dbg/frames.py <<'LSS_EOF'
from dbg.image import Inl

_maps = {}


class Map:
    def __init__(self, img):
        n = len(img.code)
        self.fn = [None] * n
        self.row = [None] * n
        self.start = [False] * n
        self.inls = [[] for _ in range(n)]
        at = {r.at: r for r in img.rows}
        for f in img.fns:
            cur = None
            for a in range(f.lo, f.hi + 1):
                self.fn[a] = f
                if a in at:
                    cur = at[a]
                    self.start[a] = True
                self.row[a] = cur
        for i in img.inls:
            for a in range(i.lo, i.hi + 1):
                self.inls[a].append(i)
        self.span = [None] * n
        for f in img.fns:
            a = f.lo
            while a <= f.hi:
                b = a + 1
                while b <= f.hi and not self.start[b]:
                    b += 1
                for c in range(a, b):
                    self.span[c] = (a, b - 1)
                a = b

    def chain(self, a):
        return [self.fn[a]] + self.inls[a]

    def line(self, a):
        r = self.row[a]
        return r.line if r else 0

    def starting(self, a):
        return [i for i in self.inls[a] if i.lo == a]


def mapping(img):
    hit = _maps.get(id(img))
    if hit is None or hit[0] is not img:
        hit = _maps[id(img)] = (img, Map(img))
    return hit[1]


def label(s):
    return s.fn.name if isinstance(s, Inl) else s.name


def show(img, pc, stack, hid):
    m = mapping(img)
    out = []
    for addr, hidden in [(pc, hid)] + [(r - 1, 0) for r in reversed(stack)]:
        ch = m.chain(addr)
        for k in range(len(ch) - 1 - hidden, -1, -1):
            line = ch[k + 1].call if k + 1 < len(ch) else m.line(addr)
            out.append((label(ch[k]), line))
    return out
LSS_EOF
cat > /app/dbg/marks.py <<'LSS_EOF'
from dbg.frames import mapping


def resolve(img, line):
    m = mapping(img)
    lowest = {}
    for r in img.rows:
        if not r.stmt or r.line != line:
            continue
        scope = m.chain(r.at)[-1]
        if id(scope) not in lowest or r.at < lowest[id(scope)]:
            lowest[id(scope)] = r.at
    return sorted(lowest.values())
LSS_EOF
cat > /app/dbg/steps.py <<'LSS_EOF'
# Correct semantics. Plants the return address to run calls, finish and cont at target speed,
# but single-steps everything inside the stepping frame, including one-line loops and the body
# of an inlined instance it steps over. The half-way family the stated limit also kills.
from dbg.frames import mapping
from dbg.image import Inl


class Stop(Exception):
    def __init__(self, kind):
        self.kind = kind


class Gone(Exception):
    pass


class Engine:
    def __init__(self, img, link, locs):
        self.img, self.link, self.locs = img, link, locs
        self.hid = 0
        self.m = mapping(img)
        self.pc = None
        self.depth = None
        self.rets = None

    def _sync(self):
        self.pc = self.link.pc()
        self.rets = self.link.stack()

    def _tick(self):
        ins = self.img.code[self.pc]
        q = self.link.step()
        if q is None:
            raise Gone()
        if ins[0] == "call":
            self.rets.append(self.pc + 1)
        elif ins[0] == "ret":
            self.rets.pop()
        self.pc = q
        if q in self.locs:
            self.hid = 0
            raise Stop("hit")

    def _wrap(self, fn):
        try:
            fn()
        except Stop as e:
            return e.kind
        except Gone:
            return None

    def run(self):
        self._sync()
        if self.pc in self.locs:
            self.hid = 0
            return "hit"
        return self.cont()

    def _run_to(self, ret, depth):
        while True:
            q = self.link.go({ret} | self.locs)
            if q is None:
                raise Gone()
            self._sync()
            if q in self.locs:
                self.hid = 0
                raise Stop("hit")
            if q == ret and len(self.rets) == depth:
                return

    def cont(self):
        q = self.link.go(self.locs)
        if q is None:
            return None
        self.hid = 0
        return "hit"

    def finish(self):
        self._sync()
        m = self.m
        ch = m.chain(self.pc)
        scope = ch[len(ch) - 1 - self.hid]
        d0 = len(self.rets)
        def body():
            if isinstance(scope, Inl):
                while True:
                    self._tick()
                    if len(self.rets) == d0 and not scope.lo <= self.pc <= scope.hi:
                        break
            else:
                self._run_to(self.rets[-1], d0 - 1)
            self.hid = len(m.starting(self.pc))
            raise Stop("done")
        return self._wrap(body)

    def step(self):
        return self._line(True)

    def next(self):
        return self._line(False)

    def _line(self, into):
        self._sync()
        m = self.m
        ch = m.chain(self.pc)
        vis = len(ch) - self.hid
        self.st = {"d": len(self.rets), "scope": ch[vis - 1],
                   "line": ch[vis].call if self.hid else m.line(self.pc), "into": into}
        if self.hid and into:
            self.hid -= 1
            return "step"
        def body():
            if self.hid:
                self.hid = 0
                self._over(ch[vis])
                self._arrive()
            while True:
                before = self.pc
                self._tick()
                d = len(self.rets)
                st = self.st
                if d > st["d"]:
                    if into and m.fn[self.pc].lines:
                        self.hid = len(m.starting(self.pc))
                        raise Stop("step")
                    ret = self.rets[-1]
                    self._run_to(ret, st["d"])
                    if m.span[self.pc] != m.span[ret - 1]:
                        self._arrive()
                elif d < st["d"]:
                    st["d"] = d
                    c2 = m.chain(self.pc)
                    st["scope"] = c2[len(c2) - 1 - len(m.starting(self.pc))]
                    self._arrive()
                elif m.span[self.pc] != m.span[before]:
                    self._arrive()
        return self._wrap(body)

    def _over(self, inst):
        d0 = self.st["d"]
        while True:
            self._tick()
            if len(self.rets) == d0 and not inst.lo <= self.pc <= inst.hi:
                return

    def _arrive(self):
        m = self.m
        while True:
            st = self.st
            q = self.pc
            s = st["scope"]
            while isinstance(s, Inl) and not s.lo <= q <= s.hi:
                s = s.up
            st["scope"] = s
            ch = m.chain(q)
            k = next(i for i, x in enumerate(ch) if x is s)
            below = [x for x in ch[k + 1:] if x.lo == q]
            if below:
                if below[0].call == st["line"]:
                    if st["into"]:
                        self.hid = len(below) - 1
                        raise Stop("step")
                    self._over(below[0])
                    continue
                self.hid = len(below)
                raise Stop("step")
            r = m.row[q]
            if r is None:
                return
            if m.start[q]:
                if r.stmt and r.line and r.line != st["line"]:
                    self.hid = 0
                    raise Stop("step")
                return
            if r.line:
                st["line"] = r.line
            return
LSS_EOF
