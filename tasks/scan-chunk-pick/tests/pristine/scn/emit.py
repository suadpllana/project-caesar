MOD = 2305843009213693951


def digest(rows):
    h = 0
    for r in rows:
        h = (h * 1000003 + r + 1) % MOD
    return h


class Out:
    __slots__ = ("lines",)

    def __init__(self):
        self.lines = []

    def qry(self, i):
        self.lines.append("qry %d" % i)

    def rd(self, c, j):
        self.lines.append("rd %d %d" % (c, j))

    def dc(self, c, j, p):
        self.lines.append("dc %d %d %d" % (c, j, p))

    def sel(self, n, h):
        self.lines.append("sel %d %d" % (n, h))

    def prj(self, c, nn, tot):
        self.lines.append("prj %d %d %d" % (c, nn, tot))
