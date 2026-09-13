"""Definitions: what was written, which layer wrote it, and which view `old` reads.

A definition carries its expression, the layer that wrote it (the number printed by `ask`),
and the view its `old` operands read in - the start of the writing layer for a plain put, the
captured pre-entry store for a mapped one. A `Move` is what a map or a tie does to the
definitions that show through it: path operands under the source are moved under the
destination, and each distinct source definition becomes exactly one moved definition, so
identity - which the memo and the circularity check key on - survives the move.
"""


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


class Move:
    """One installation: a source prefix, a destination prefix, and the definitions it made.

    `prior` is None for a tie, which leaves each definition the view it already has, and the
    captured root for a map, which gives every definition it makes that view instead.
    """
    __slots__ = ("src", "dst", "prior", "defs", "home")

    def __init__(self, src, dst, prior, home=None):
        self.src, self.dst, self.prior, self.home = src, dst, prior, home
        self.defs = {}

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
            got = Dfn(self.expr(dfn.expr), dfn.home if self.home is None else self.home,
                      dfn.prior if self.prior is None else self.prior)
            self.defs[dfn] = got
        return got
