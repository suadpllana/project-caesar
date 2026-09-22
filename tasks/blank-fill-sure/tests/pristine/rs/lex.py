import re

INT = re.compile(r"(0|[1-9][0-9]{0,8})$")
SYM = re.compile(r"[a-z][a-z0-9_]*$")
VAR = re.compile(r"[A-Z][A-Za-z0-9_]*$")
TAG = re.compile(r"\?[a-z0-9_]+$")


class Blank:
    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


def const(tok):
    if INT.match(tok):
        return int(tok)
    if SYM.match(tok):
        return tok
    raise ValueError("not a constant: %r" % tok)


def value(tok, blanks):
    if TAG.match(tok):
        b = blanks.get(tok)
        if b is None:
            b = blanks[tok] = Blank(tok)
        return b
    return const(tok)
