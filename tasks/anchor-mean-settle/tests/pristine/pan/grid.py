from pan import gues, mtr


class Row:
    __slots__ = ("rid", "ln", "hm")

    def __init__(self, rid, ln):
        self.rid = rid
        self.ln = ln
        self.hm = None


class Pan:
    __slots__ = ("rows", "w", "top", "anc", "dy", "made")

    def __init__(self):
        self.rows = []
        self.w = mtr.W0
        self.top = 0
        self.anc = -1
        self.dy = 0
        self.made = 0


def new():
    return Pan()


def find(p, rid):
    for i, r in enumerate(p.rows):
        if r.rid == rid:
            return i
    return -1


def hgt(p, r):
    return r.hm if r.hm is not None else gues.hei(p)


def off(p, k):
    a = 0
    for r in p.rows[:k]:
        a += hgt(p, r)
    return a


def hit(p):
    a = 0
    for i, r in enumerate(p.rows):
        if a >= p.top:
            return i
        a += hgt(p, r)
    return len(p.rows) - 1


def view(p):
    a = 0
    out = []
    stop = p.top + mtr.VIEW
    for i, r in enumerate(p.rows):
        if a >= stop:
            break
        h = hgt(p, r)
        if a + h > p.top:
            out.append(i)
        a += h
    return out


def mark(p, k):
    r = p.rows[k]
    r.hm = mtr.high(r.ln, p.w)
