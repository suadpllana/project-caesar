from st import ext


class Fil:
    __slots__ = ("s",)

    def __init__(self, n):
        self.s = [None] * n


class Vol:
    __slots__ = ("f",)

    def __init__(self):
        self.f = {}


class Store:
    def __init__(self):
        self.v = {}
        self.e = {}
        self.nid = 1
        self.out = []
        ext.boot(self)
