from . import addr, grid, memo, see


class Run:
    def __init__(self, sink):
        self.sink = sink
        self.sheet = grid.Sheet()
        self.n = 0

    def step(self, verb, tail):
        self.n += 1
        if verb == "put":
            at = addr.parse(tail[0])
            self.sheet.put(at, " ".join(tail[1:]))
        elif verb == "clr":
            at = addr.parse(tail[0])
            self.sheet.clr(at)
        else:
            raise ValueError(verb)
        st = memo.State(self.sheet)
        parts = []
        for a in addr.walk():
            v = see.face(st, a)
            txt = grid.show(v)
            if txt:
                parts.append("%s=%s" % (addr.name(a), txt))
        self.sink((self.n, verb, tail[0], " ".join(parts)))

    def run(self, lines):
        for raw in lines:
            toks = raw.split()
            if not toks:
                continue
            self.step(toks[0], toks[1:])
