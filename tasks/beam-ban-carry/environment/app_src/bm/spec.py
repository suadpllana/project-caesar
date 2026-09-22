class Spec:
    __slots__ = ("w", "n", "s", "p", "h", "t", "rows", "asks")

    def __init__(self):
        self.w = 1
        self.n = 2
        self.s = 1
        self.p = 0
        self.h = 1
        self.t = 1
        self.rows = []
        self.asks = []


def parse(text):
    sp = Spec()
    for raw in text.splitlines():
        part = raw.split()
        if not part:
            continue
        head = part[0]
        if head == "cfg":
            sp.w, sp.n, sp.s, sp.p, sp.h, sp.t = (int(x) for x in part[1:7])
        elif head == "sc":
            sp.rows.append((int(part[1]), int(part[2]), int(part[3])))
        elif head == "ask":
            sp.asks.append((part[1], tuple(int(x) for x in part[2:])))
    return sp
