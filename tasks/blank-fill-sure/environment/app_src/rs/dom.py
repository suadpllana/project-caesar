from rs import lex

TOP = 999999999


class Span:
    __slots__ = ("lo", "hi")

    def __init__(self, lo, hi):
        self.lo = lo
        self.hi = hi

    def has(self, v):
        return type(v) is int and self.lo <= v <= self.hi


class Pick:
    __slots__ = ("syms",)

    def __init__(self, syms):
        self.syms = syms

    def has(self, v):
        return type(v) is str and v in self.syms


def parse(tok):
    if ".." in tok:
        a, b = tok.split("..", 1)
        lo, hi = lex.const(a), lex.const(b)
        if type(lo) is not int or type(hi) is not int or lo > hi or hi > TOP:
            raise ValueError("bad range: %r" % tok)
        return Span(lo, hi)
    syms = tok.split("|")
    if len(set(syms)) != len(syms) or not all(lex.SYM.match(s) for s in syms):
        raise ValueError("bad list: %r" % tok)
    return Pick(tuple(syms))
