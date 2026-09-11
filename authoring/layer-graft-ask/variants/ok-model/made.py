"""A definition, and what a copy hands on: the same object, unchanged."""


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
