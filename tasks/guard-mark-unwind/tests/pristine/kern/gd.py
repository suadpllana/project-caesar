class Gd:
    __slots__ = ("lbl", "dl", "sh", "hit", "src", "own", "cl", "end", "kind")

    def __init__(self, lbl, dl, sh, own, end, kind):
        self.lbl = lbl
        self.dl = dl
        self.sh = sh
        self.hit = False
        self.src = None
        self.own = own
        self.cl = None
        self.end = end
        self.kind = kind


class Bd:
    __slots__ = ("lbl", "own", "gd", "kids", "errs", "end", "inh")

    def __init__(self, lbl, own, gd, end, inh):
        self.lbl = lbl
        self.own = own
        self.gd = gd
        self.kids = []
        self.errs = []
        self.end = end
        self.inh = inh


def chain(f):
    out = list(f.inh)
    for e in f.bl:
        out.append(e[1] if e[0] == "g" else e[1].gd)
    return out


def inner(f):
    if not f.bl:
        return None
    e = f.bl[-1]
    return e[1] if e[0] == "g" else e[1].gd


def busy(bd):
    n = 0
    for k in bd.kids:
        if k.st != 2:
            n += 1
    return n
