"""What a definition is, and what happens to one when a copy hands it on.

A definition is the expression a `put` wrote together with the layer that wrote it. That
layer is two things at once: the stop a backward reference inside the expression is answered
at, and the layer a query reports. A copy changes neither, so `carried` hands the subtree back
exactly as it found it - which is also why a copy can be one node reference: there is nothing
to rebuild.
"""


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
