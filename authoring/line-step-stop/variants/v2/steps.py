# Correct variant V2: plants every decision address of the stepping function (row starts,
# branch targets, call targets) except the current row's own, tracks depth by decoding what
# the target stopped on, and ends a command by raising.
from dbg.frames import tree
from dbg.image import Inl


class Done(Exception):
    def __init__(self, kind):
        self.kind = kind


class Engine:
    def __init__(self, img, link, locs):
        self.img, self.link, self.locs = img, link, locs
        self.hid = 0
        self.t = tree(img)
        self.marks = {}
        for f in img.fns:
            s = set()
            for r in img.rows:
                if f.lo <= r.at <= f.hi:
                    s.add(r.at)
            for a in range(f.lo, f.hi + 1):
                ins = img.code[a]
                if ins[0] == "jmp":
                    s.add(ins[1])
                elif ins[0] == "jnz":
                    s.add(ins[2])
                    s.add(a + 1)
                elif ins[0] == "call":
                    s.add(ins[1])
            self.marks[f.name] = s

    def _stop_on(self, stops):
        q = self.link.go(stops | self.locs)
        if q is None:
            raise Done(None)
        if q in self.locs:
            self.hid = 0
            raise Done("hit")
        return q, len(self.link.stack())

    def _exec(self, fn):
        try:
            fn()
        except Done as d:
            return d.kind
        raise AssertionError("command ended without a stop")

    def run(self):
        if self.link.pc() in self.locs:
            self.hid = 0
            return "hit"
        return self.cont()

    def cont(self):
        return self._exec(lambda: self._stop_on(set()))

    def finish(self):
        def body():
            pc = self.link.pc()
            stack = self.link.stack()
            sc = self.t.scopes(pc)
            top = sc[len(sc) - 1 - self.hid]
            depth = len(stack)
            if isinstance(top, Inl):
                q = self._leave(top, depth)
            else:
                while True:
                    q, d = self._stop_on({stack[-1]})
                    if q == stack[-1] and d == depth - 1:
                        break
            self.hid = sum(1 for s in self.t.scopes(q) if isinstance(s, Inl) and s.lo == q)
            raise Done("done")
        return self._exec(body)

    def _leave(self, inst, depth):
        while True:
            q, d = self._stop_on({inst.hi + 1})
            if q == inst.hi + 1 and d == depth:
                return q

    def step(self):
        return self._exec(lambda: self._walk(True))

    def next(self):
        return self._exec(lambda: self._walk(False))

    def _row_span(self, addr):
        f = self.img.fn_at(addr)
        r = self.t.row(addr)
        if r is None:
            return f.lo, f.hi
        nxt = [x.at for x in self.img.rows if r.at < x.at <= f.hi]
        return r.at, (min(nxt) - 1 if nxt else f.hi)

    def _walk(self, into):
        pc = self.link.pc()
        stack = self.link.stack()
        sc = self.t.scopes(pc)
        vis = len(sc) - self.hid
        self.into = into
        self.depth = len(stack)
        self.scope = sc[vis - 1]
        self.line = sc[vis].call if self.hid else self.t.line(pc)
        if self.hid:
            if into:
                self.hid -= 1
                raise Done("step")
            self.hid = 0
            pc = self._judge(self._leave(sc[vis], self.depth))
        while True:
            lo, hi = self._row_span(pc)
            f = self.img.fn_at(pc)
            stops = {a for a in self.marks[f.name] if not lo <= a <= hi}
            for a in range(lo, hi + 1):
                if self.img.code[a][0] == "call":
                    stops.add(self.img.code[a][1])
            stack = self.link.stack()
            if stack:
                stops.add(stack[-1])
            q, d = self._stop_on(stops)
            if d > self.depth:
                if into and self.img.fn_at(q).lines:
                    self.hid = sum(1 for s in self.t.scopes(q) if isinstance(s, Inl) and s.lo == q)
                    raise Done("step")
                ret = self.link.stack()[-1]
                while True:
                    q, d2 = self._stop_on({ret})
                    if q == ret and d2 == self.depth:
                        break
                if self._row_span(q) == (lo, hi):
                    pc = q
                    continue
            elif d < self.depth:
                self.depth = d
                sc2 = self.t.scopes(q)
                n_start = sum(1 for s in sc2 if isinstance(s, Inl) and s.lo == q)
                self.scope = sc2[len(sc2) - 1 - n_start]
            elif lo <= q <= hi:
                pc = q
                continue
            pc = self._judge(q)

    def _judge(self, q):
        while True:
            s = self.scope
            while isinstance(s, Inl) and not s.lo <= q <= s.hi:
                s = s.up
            self.scope = s
            sc = self.t.scopes(q)
            pos = [i for i, x in enumerate(sc) if x is s][0]
            fresh = [x for x in sc[pos + 1:] if x.lo == q]
            if fresh:
                if fresh[0].call == self.line:
                    if self.into:
                        self.hid = len(fresh) - 1
                        raise Done("step")
                    q = self._leave(fresh[0], self.depth)
                    continue
                self.hid = len(fresh)
                raise Done("step")
            r = self.t.row(q)
            if r is None:
                return q
            if r.at == q:
                if r.stmt and r.line and r.line != self.line:
                    self.hid = 0
                    raise Done("step")
                return q
            if r.line:
                self.line = r.line
            return q
