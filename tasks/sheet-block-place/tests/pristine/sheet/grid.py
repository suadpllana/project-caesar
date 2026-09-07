from . import form

EMPTY = ("gap",)
CYC = ("err", "#cyc")
REF = ("err", "#ref")
BLK = ("err", "#blk")


def is_num(v):
    return type(v) is int


def is_gap(v):
    return v is EMPTY


def is_err(v):
    return type(v) is tuple and v[0] == "err"


def is_blk(v):
    return type(v) is tuple and v[0] == "blk"


def is_set(v):
    return type(v) is tuple and v[0] == "set"


def blk(h, w, items):
    return ("blk", h, w, tuple(items))


def bag(h, w, items):
    return ("set", h, w, tuple(items))


def items(v):
    if is_blk(v) or is_set(v):
        return v[3]
    return (v,)


def shape(v):
    if is_blk(v) or is_set(v):
        return (v[1], v[2])
    return (1, 1)


def size(v):
    if is_blk(v) or is_set(v):
        return v[1] * v[2]
    return 1


def show(v):
    if is_num(v):
        return str(v)
    if is_err(v):
        return v[1]
    return ""


class Sheet:
    def __init__(self):
        self.cells = {}
        self.order = []

    def put(self, a, text):
        node = form.build(text)
        if a not in self.cells:
            self.order.append(a)
            self.order.sort()
        self.cells[a] = (text, node)

    def clr(self, a):
        if a in self.cells:
            del self.cells[a]
            self.order.remove(a)

    def held(self, a):
        return a in self.cells

    def node(self, a):
        return self.cells[a][1]

    def owners(self):
        return list(self.order)
