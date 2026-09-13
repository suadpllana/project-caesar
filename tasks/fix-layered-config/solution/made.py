"""Binding origin, predecessor view, and one template installation."""

class Dfn:
    __slots__ = ("expr", "home", "prior")

    def __init__(self, expr, home, prior):
        self.expr = expr
        self.home = home
        self.prior = prior


def make(expr, home):
    return Dfn(expr, home, home)


def back(dfn):
    return dfn.prior


def reported(dfn):
    return dfn.home


def carried(sub, at):
    return sub


class Frame:
    __slots__ = ("src", "dst", "view", "defs", "nodes")

    def __init__(self, src, dst, view):
        self.src, self.dst, self.view = src, dst, view
        self.defs, self.nodes = {}, {}

    def path(self, path):
        n = len(self.src)
        return self.dst + path[n:] if path[:n] == self.src else path

    def expr(self, expr):
        tag = expr[0]
        if tag == "lit":
            return expr
        if tag in ("now", "old"):
            return (tag, self.path(expr[1]))
        if tag == "pick":
            return (tag, self.path(expr[1]), self.expr(expr[2]), self.expr(expr[3]))
        return (tag, self.expr(expr[1]), self.expr(expr[2]))

    def bind(self, dfn):
        if dfn is None:
            return None
        got = self.defs.get(dfn)
        if got is None:
            got = Dfn(self.expr(dfn.expr), dfn.home, self.view)
            self.defs[dfn] = got
        return got
