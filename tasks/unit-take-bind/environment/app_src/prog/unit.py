class Unit:
    __slots__ = ("nm", "owns", "als", "pulls", "shuts", "hides")

    def __init__(self, nm):
        self.nm = nm
        self.owns = []
        self.als = []
        self.pulls = []
        self.shuts = set()
        self.hides = set()


class Prog:
    __slots__ = ("units", "asks")

    def __init__(self):
        self.units = {}
        self.asks = []


def own_unit(prog, nm):
    u = prog.units.get(nm)
    if u is None:
        u = Unit(nm)
        prog.units[nm] = u
    return u


def find(prog, nm):
    return prog.units.get(nm)
