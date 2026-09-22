class Book:
    """The span numbering for one request. A span gets a bit the first time it is recorded."""

    __slots__ = ("n", "num")

    def __init__(self, n):
        self.n = n
        self.num = {}

    def find(self, span):
        return self.num.get(span, -1)

    def mark(self, span):
        bit = self.num.get(span)
        if bit is None:
            bit = len(self.num)
            self.num[span] = bit
        return bit


class Path:
    """A beam's sequence, kept as a link to its parent, and the spans that sequence holds."""

    __slots__ = ("prev", "tok", "last", "tail", "mask", "length")

    def __init__(self, prev, tok, last, tail, mask, length):
        self.prev = prev
        self.tok = tok
        self.last = last
        self.tail = tail
        self.mask = mask
        self.length = length

    def holds(self, bit):
        return bit >= 0 and (self.mask >> bit) & 1

    def tokens(self):
        out, here = [], self
        while here.prev is not None:
            out.append(here.tok)
            here = here.prev
        out.reverse()
        return out


def root(book, prompt):
    n = book.n
    mask = 0
    for i in range(len(prompt) - n + 1):
        mask |= 1 << book.mark(tuple(prompt[i:i + n]))
    tail = tuple(prompt[1 - n:]) if n > 1 else ()
    return Path(None, None, prompt[-1], tail, mask, 0)


def reach(book, path, tok):
    """The span a continuation would add, as a bit, or -1 while the sequence is too short."""
    if len(path.tail) < book.n - 1:
        return -1
    return book.find(path.tail + (tok,))


def grow(book, path, tok):
    mask = path.mask
    if len(path.tail) >= book.n - 1:
        mask |= 1 << book.mark(path.tail + (tok,))
    tail = (path.tail + (tok,))[1 - book.n:] if book.n > 1 else ()
    return Path(path, tok, tok, tail, mask, path.length + 1)


class Lent:
    """What the kept set lends the search: the spans of its members, combined."""

    __slots__ = ("mask",)

    def __init__(self):
        self.mask = 0

    def reset(self, masks):
        one = 0
        for mask in masks:
            one |= mask
        self.mask = one

    def has(self, bit):
        return bit >= 0 and (self.mask >> bit) & 1
