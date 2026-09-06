class Nd:
    __slots__ = ("wid", "par", "kids", "fl", "grp", "scr")

    def __init__(self, wid, par, fl, grp, scr):
        self.wid = wid
        self.par = par
        self.kids = []
        self.fl = fl
        self.grp = grp
        self.scr = scr


class Scr:
    __slots__ = ("nm", "root")

    def __init__(self, nm):
        self.nm = nm
        self.root = Nd(nm, None, set(), None, self)


class Ev:
    __slots__ = ("k", "w", "s", "p", "nm", "at", "fl", "grp")

    def __init__(self, k):
        self.k = k
        self.w = None
        self.s = None
        self.p = None
        self.nm = None
        self.at = None
        self.fl = None
        self.grp = None
