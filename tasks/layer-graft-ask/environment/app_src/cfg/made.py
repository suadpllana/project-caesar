class Dfn:
    __slots__ = ("expr", "home")

    def __init__(self, expr, home):
        self.expr = expr
        self.home = home


def make(expr, home):
    return Dfn(expr, home)


def carried(dfn, at):
    return Dfn(dfn.expr, at)


def back(dfn):
    return dfn.home


def reported(dfn):
    return dfn.home
