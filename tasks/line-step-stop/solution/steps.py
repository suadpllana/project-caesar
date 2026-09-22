from dbg.frames import mapping
from dbg.image import Inl

GONE = object()


class Engine:
    def __init__(self, img, link, locs):
        self.img = img
        self.link = link
        self.locs = locs
        self.hid = 0
        self.m = mapping(img)
        self._exits = {}

    def _go(self, stops):
        return self.link.go(stops | self.locs)

    def _depth(self):
        return len(self.link.stack())

    def run(self):
        if self.link.pc() in self.locs:
            self.hid = 0
            return "hit"
        return self.cont()

    def cont(self):
        if self._go(set()) is None:
            return None
        self.hid = 0
        return "hit"

    def finish(self):
        m = self.m
        pc = self.link.pc()
        stack = self.link.stack()
        ch = m.chain(pc)
        scope = ch[len(ch) - 1 - self.hid]
        depth = len(stack)
        if isinstance(scope, Inl):
            out = self._leave(scope, depth)
            if not isinstance(out, int):
                return self._end(out)
            q = out
        else:
            ret = stack[-1]
            while True:
                q = self._go({ret})
                if q is None:
                    return None
                if q in self.locs:
                    self.hid = 0
                    return "hit"
                if q == ret and self._depth() == depth - 1:
                    break
        self.hid = len(m.starting(q))
        return "done"

    def step(self):
        return self._line(True)

    def next(self):
        return self._line(False)

    def _end(self, out):
        return None if out is GONE else out

    def _leave(self, inst, depth):
        stops = {inst.hi + 1}
        while True:
            q = self._go(stops)
            if q is None:
                return GONE
            if q in self.locs:
                self.hid = 0
                return "hit"
            if q == inst.hi + 1 and self._depth() == depth:
                return q

    def _line(self, into):
        m = self.m
        pc = self.link.pc()
        stack = self.link.stack()
        ch = m.chain(pc)
        vis = len(ch) - self.hid
        self.into = into
        self.depth = len(stack)
        self.scope = ch[vis - 1]
        self.line = ch[vis].call if self.hid else m.line(pc)
        if self.hid:
            if into:
                self.hid -= 1
                return "step"
            self.hid = 0
            out = self._leave(ch[vis], self.depth)
            if not isinstance(out, int):
                return self._end(out)
            pc = out
            out = self._judge(pc)
            if not isinstance(out, int):
                return self._end(out)
            pc = out
        return self._range(pc)

    def _row_exits(self, lo, hi):
        key = (lo, hi)
        got = self._exits.get(key)
        if got is None:
            code = self.img.code
            exits = set()
            has_ret = False
            for a in range(lo, hi + 1):
                ins = code[a]
                op = ins[0]
                if op == "jmp":
                    if not lo <= ins[1] <= hi:
                        exits.add(ins[1])
                elif op == "jnz":
                    if not lo <= ins[2] <= hi:
                        exits.add(ins[2])
                    if not lo <= a + 1 <= hi:
                        exits.add(a + 1)
                elif op == "call":
                    exits.add(ins[1])
                elif op == "ret":
                    has_ret = True
                elif not lo <= a + 1 <= hi:
                    exits.add(a + 1)
            got = self._exits[key] = (exits, has_ret)
        return got

    def _range(self, pc):
        m = self.m
        while True:
            lo, hi = m.span[pc]
            exits, has_ret = self._row_exits(lo, hi)
            stops = exits
            if has_ret:
                stack = self.link.stack()
                if stack:
                    stops = exits | {stack[-1]}
            q = self._go(stops)
            if q is None:
                return None
            if q in self.locs:
                self.hid = 0
                return "hit"
            d = self._depth()
            if d > self.depth:
                if self.into and m.fn[q].lines:
                    self.hid = len(m.starting(q))
                    return "step"
                ret = self.link.stack()[-1]
                while True:
                    q = self._go({ret})
                    if q is None:
                        return None
                    if q in self.locs:
                        self.hid = 0
                        return "hit"
                    if q == ret and self._depth() == self.depth:
                        break
                if lo <= q <= hi:
                    pc = q
                    continue
            elif d < self.depth:
                self.depth = d
                ch = m.chain(q)
                self.scope = ch[len(ch) - 1 - len(m.starting(q))]
            elif lo <= q <= hi:
                pc = q
                continue
            out = self._judge(q)
            if not isinstance(out, int):
                return self._end(out)
            pc = out

    def _judge(self, q):
        m = self.m
        while True:
            scope = self.scope
            while isinstance(scope, Inl) and not scope.lo <= q <= scope.hi:
                scope = scope.up
            self.scope = scope
            ch = m.chain(q)
            k = next(i for i, s in enumerate(ch) if s is scope)
            below = [s for s in ch[k + 1:] if s.lo == q]
            if below:
                if below[0].call == self.line:
                    if self.into:
                        self.hid = len(below) - 1
                        return "step"
                    out = self._leave(below[0], self.depth)
                    if not isinstance(out, int):
                        return out
                    q = out
                    continue
                self.hid = len(below)
                return "step"
            r = m.row[q]
            if r is None:
                return q
            if m.start[q]:
                if r.stmt and r.line and r.line != self.line:
                    self.hid = 0
                    return "step"
                return q
            if r.line:
                self.line = r.line
            return q
