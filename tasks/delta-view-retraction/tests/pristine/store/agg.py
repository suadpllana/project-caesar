SUM = "sum"
CNT = "cnt"
MIN = "min"
MAX = "max"
TOP = "top"

KINDS = (SUM, CNT, MIN, MAX, TOP)

CAP = 3

JRN = []


class Acc:
    __slots__ = ("kind", "s", "n", "top")

    def __init__(self, kind):
        self.kind = kind
        self.s = 0
        self.n = 0
        self.top = {}

    def copy(self):
        a = Acc(self.kind)
        a.s = self.s
        a.n = self.n
        a.top = dict(self.top)
        return a


def blank(kind):
    return Acc(kind)


def _rank(kind, v):
    if kind == MAX or kind == TOP:
        return -v
    return v


def _refresh(acc):
    k = acc.kind
    if not acc.top:
        acc.s = 0
        return
    order = sorted(acc.top, key=lambda v: _rank(k, v))
    if k == MIN or k == MAX:
        acc.s = order[0]
    elif k == TOP:
        acc.s = sum(order[:2])


def fold(acc, v, w):
    JRN.append((acc.kind, v, w))
    k = acc.kind
    if k == SUM:
        acc.s += v * w
        acc.n += w
        return acc
    if k == CNT:
        acc.n += w
        acc.s = acc.n
        return acc
    acc.n += w
    if v in acc.top:
        c = acc.top[v] + w
        if c <= 0:
            acc.top.pop(v, None)
        else:
            acc.top[v] = c
    elif w > 0:
        acc.top[v] = w
        if len(acc.top) > CAP:
            order = sorted(acc.top, key=lambda x: _rank(k, x))
            for x in order[CAP:]:
                acc.top.pop(x, None)
    _refresh(acc)
    return acc


def value(acc):
    return acc.s
