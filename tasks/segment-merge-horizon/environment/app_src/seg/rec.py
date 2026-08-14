PUT = 0
DEL = 1
ADD = 2

KINDS = (PUT, DEL, ADD)


class Rec:
    __slots__ = ("k", "s", "t", "v")

    def __init__(self, k, s, t, v):
        self.k = k
        self.s = s
        self.t = t
        self.v = v

    def row(self):
        return [self.k, self.s, self.t, self.v]

    def copy(self):
        return Rec(self.k, self.s, self.t, self.v)

    def __repr__(self):
        return "R(k=%d s=%d t=%d v=%d)" % (self.k, self.s, self.t, self.v)
