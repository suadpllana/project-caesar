"""A definition and the layer that wrote it, with a copy changing neither."""


class Dfn:
    __slots__ = ("expr", "home")

    def __init__(self, expr, home):
        self.expr = expr
        self.home = home


def make(expr, home):
    return Dfn(expr, home)


def carried(sub, at):
    return sub


def back(dfn):
    return dfn.home


def reported(dfn):
    return dfn.home
