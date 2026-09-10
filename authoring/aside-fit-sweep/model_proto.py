"""Independent brute-force model: a granule array and linear scans."""
FREE, USED, SIDE = 0, 1, 2
GRAIN, SLIVER, KEEP, ROOM = 8, 16, 256, 32


def up(n):
    return (n + GRAIN - 1) // GRAIN * GRAIN


class M:
    def __init__(self, span, part):
        self.span, self.part = span, part
        self.g = bytearray(span // GRAIN)
        self.ids = {}
        self.aside = []

    def paint(self, a, n, st):
        for i in range(a // GRAIN, (a + n) // GRAIN):
            self.g[i] = st

    def free_at(self, a, n):
        return all(self.g[i] == FREE for i in range(a // GRAIN, (a + n) // GRAIN))

    def spot(self, n):
        a = 0
        while a + n <= self.span:
            if a % self.part + n <= self.part and self.free_at(a, n):
                return a
            a += GRAIN
        return None

    def after(self, a, n):
        stop = (a // self.part + 1) * self.part
        x, c = a + n, 0
        while x < stop and self.g[x // GRAIN] == FREE:
            c += GRAIN
            x += GRAIN
        return c

    def flush(self):
        for a, n in self.aside:
            self.paint(a, n, FREE)
        self.aside = []

    def park(self, a, n):
        self.paint(a, n, SIDE)
        self.aside.append((a, n))
        while len(self.aside) > ROOM:
            oa, on = self.aside.pop(0)
            self.paint(oa, on, FREE)

    def give(self, a, n):
        if n <= KEEP:
            self.park(a, n)
        else:
            self.paint(a, n, FREE)

    def grab(self, n):
        for i in range(len(self.aside) - 1, -1, -1):
            if self.aside[i][1] == n:
                a, sz = self.aside.pop(i)
                self.paint(a, sz, USED)
                return a, sz
        a = self.spot(n)
        if a is None:
            self.flush()
            a = self.spot(n)
            if a is None:
                return None
        t = self.after(a, n)
        sz = n + t if 0 < t < SLIVER else n
        self.paint(a, sz, USED)
        return a, sz


def expect(lines):
    span = part = 0
    body = []
    for raw in lines:
        b = raw.split()
        if not b:
            continue
        if b[0] == "span":
            span = int(b[1])
        elif b[0] == "part":
            part = int(b[1])
        else:
            body.append(b)
    m = M(span, part)
    out = []
    for b in body:
        op = b[0]
        if op == "get":
            name, sz = b[1], int(b[2])
            if name in m.ids:
                continue
            n = up(sz)
            if not (0 < n <= part):
                out.append("no %s" % name)
                continue
            got = m.grab(n)
            if got is None:
                out.append("no %s" % name)
                continue
            m.ids[name] = got
            out.append("at %s %d %d" % (name, got[0], got[1]))
        elif op == "put":
            name = b[1]
            if name not in m.ids:
                continue
            a, n = m.ids.pop(name)
            m.give(a, n)
        elif op == "fit":
            name, sz = b[1], int(b[2])
            if name not in m.ids:
                continue
            n = up(sz)
            if not (0 < n <= part):
                out.append("no %s" % name)
                continue
            a, cur = m.ids[name]
            if n <= cur:
                if cur - n < SLIVER:
                    out.append("same %s %d" % (name, cur))
                else:
                    m.paint(a + n, cur - n, FREE)
                    m.ids[name] = (a, n)
                    m.give(a + n, cur - n)
                    out.append("same %s %d" % (name, n))
                continue
            stop = (a // part + 1) * part
            if a + n <= stop and m.free_at(a + cur, n - cur):
                t = m.after(a, n)
                sz2 = n + t if 0 < t < SLIVER else n
                m.paint(a, sz2, USED)
                m.ids[name] = (a, sz2)
                out.append("same %s %d" % (name, sz2))
                continue
            got = m.grab(n)
            if got is None:
                out.append("no %s" % name)
                continue
            m.paint(a, cur, FREE)
            m.give(a, cur)
            m.ids[name] = got
            out.append("at %s %d %d" % (name, got[0], got[1]))
        elif op == "sweep":
            m.flush()
    return out
