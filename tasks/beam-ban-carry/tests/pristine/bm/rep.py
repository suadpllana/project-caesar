class Path:
    __slots__ = ("seq", "n", "cut")

    def __init__(self, seq, n, cut):
        self.seq = seq
        self.n = n
        self.cut = cut

    @property
    def last(self):
        return self.seq[-1]

    @property
    def length(self):
        return len(self.seq) - self.cut

    def span(self, tok):
        if len(self.seq) + 1 < self.n:
            return None
        return tuple(self.seq[len(self.seq) + 1 - self.n:]) + (tok,)

    def holds(self, span):
        n = self.n
        seq = self.seq
        for i in range(len(seq) - n + 1):
            if tuple(seq[i:i + n]) == span:
                return True
        return False

    def spans(self):
        n = self.n
        seq = self.seq
        return [tuple(seq[i:i + n]) for i in range(len(seq) - n + 1)]

    def plus(self, tok):
        return Path(self.seq + [tok], self.n, self.cut)

    def tokens(self):
        return self.seq[self.cut:]


def root(prompt, n):
    return Path(list(prompt), n, len(prompt))


class Lent:
    __slots__ = ("seen",)

    def __init__(self):
        self.seen = set()

    def take(self, path):
        for one in path.spans():
            self.seen.add(one)

    def give(self, path):
        return None

    def has(self, span):
        return span in self.seen
