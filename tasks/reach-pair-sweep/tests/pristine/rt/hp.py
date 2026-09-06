class Ob:
    __slots__ = ("fl", "fz")

    def __init__(self, fz):
        self.fl = {}
        self.fz = fz


class Wk:
    __slots__ = ("t", "c")

    def __init__(self, t):
        self.t = t
        self.c = False


class Hp:
    __slots__ = ("ob", "fr", "wk", "pr", "qu", "rn")

    def __init__(self):
        self.ob = {}
        self.fr = [{}]
        self.wk = {}
        self.pr = []
        self.qu = []
        self.rn = set()
