class D:
    __slots__ = ("up", "ent")

    def __init__(self, up):
        self.up = up
        self.ent = {}


class It:
    __slots__ = ("tag", "nl", "hld")

    def __init__(self, tag):
        self.tag = tag
        self.nl = 0
        self.hld = False


class St:
    __slots__ = ("dirs", "itm", "blob", "roots", "spn", "lim", "age", "nd", "used",
                 "bx", "log", "marks")

    def __init__(self):
        self.dirs = {}
        self.itm = {}
        self.blob = {}
        self.roots = {}
        self.spn = {}
        self.lim = {}
        self.age = 0
        self.nd = 0
        self.used = set()
        self.bx = {}
        self.log = []
        self.marks = []

    def space(self, nm, cap):
        self.nd += 1
        self.dirs[self.nd] = D(None)
        self.roots[nm] = self.nd
        self.spn[self.nd] = nm
        self.lim[nm] = cap
        return self.nd

    def fresh(self):
        self.nd += 1
        return self.nd
