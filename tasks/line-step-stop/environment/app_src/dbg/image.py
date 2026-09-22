import bisect


class Fn:
    __slots__ = ("name", "lo", "hi", "lines")

    def __init__(self, name, lo, hi, lines):
        self.name = name
        self.lo = lo
        self.hi = hi
        self.lines = lines


class Row:
    __slots__ = ("at", "line", "stmt")

    def __init__(self, at, line, stmt):
        self.at = at
        self.line = line
        self.stmt = stmt


class Inl:
    __slots__ = ("id", "fn", "up", "call", "lo", "hi")

    def __init__(self, id, fn, up, call, lo, hi):
        self.id = id
        self.fn = fn
        self.up = up
        self.call = call
        self.lo = lo
        self.hi = hi


class Image:
    def __init__(self, text):
        self.fns = []
        self.code = []
        self.rows = []
        self.inls = []
        self.by_id = {}
        for raw in text.splitlines():
            w = raw.split()
            if not w:
                continue
            if w[0] == "fn":
                lines = (int(w[4]), int(w[5])) if len(w) > 4 else None
                self.fns.append(Fn(w[1], int(w[2]), int(w[3]), lines))
            elif w[0] == "row":
                self.rows.append(Row(int(w[1]), int(w[2]), len(w) < 4))
            elif w[0] == "inl":
                up = w[3]
                if up.isdigit():
                    up = self.by_id[int(up)]
                else:
                    up = self.fn(up)
                i = Inl(int(w[1]), self.fn(w[2]), up, int(w[4]), int(w[5]), int(w[6]))
                self.inls.append(i)
                self.by_id[i.id] = i
            elif w[0].isdigit():
                op = w[1]
                args = tuple(a if a.isalpha() else int(a) for a in w[2:])
                self.code.append((op,) + args)
        self._los = [f.lo for f in self.fns]

    def fn(self, name):
        for f in self.fns:
            if f.name == name:
                return f
        raise KeyError(name)

    def fn_at(self, addr):
        return self.fns[bisect.bisect_right(self._los, addr) - 1]


def load(path):
    with open(path) as f:
        return Image(f.read())
