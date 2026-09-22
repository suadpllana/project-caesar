class Path:
    """A link back to the parent for the tokens, and a dict of the spans held."""

    __slots__ = ("back", "tok", "last", "run", "held", "length")

    def __init__(self, back, tok, last, run, held, length):
        self.back = back
        self.tok = tok
        self.last = last
        self.run = run
        self.held = held
        self.length = length

    def tokens(self):
        got, at = [], self
        while at.back is not None:
            got.append(at.tok)
            at = at.back
        return got[::-1]


def root(prompt, n):
    run = tuple(prompt)
    held = {}
    for i in range(len(run) - n + 1):
        held[run[i:i + n]] = 1
    return Path(None, None, run[-1], run[max(0, len(run) - n + 1):], held, 0)


def span_of(path, n, tok):
    if len(path.run) + 1 < n:
        return None
    return path.run + (tok,)


def grow(path, n, tok):
    span = span_of(path, n, tok)
    held = path.held
    if span is not None:
        held = dict(held)
        held[span] = 1
    run = (path.run + (tok,))
    if len(run) > n - 1:
        run = run[len(run) - n + 1:]
    return Path(path, tok, tok, run, held, path.length + 1)


class Lent:
    """The members' own dicts, asked in turn; nothing is merged and nothing is counted."""

    __slots__ = ("mine",)

    def __init__(self):
        self.mine = []

    def reset(self, held):
        self.mine = list(held)

    def has(self, span):
        for one in self.mine:
            if span in one:
                return True
        return False
