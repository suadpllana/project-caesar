# wrong reading: caller frames are shown at the return address instead of the call instruction
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
    for addr, hidden in [(pc, hid)] + [(r, 0) for r in reversed(stack)]:
        ch = m.chain(addr)
        for k in range(len(ch) - 1 - hidden, -1, -1):
            line = ch[k + 1].call if k + 1 < len(ch) else m.line(addr)
            out.append((label(ch[k]), line))
    return out
