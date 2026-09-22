class Path:
    """Whole token tuple, with the spans it holds as a frozenset beside it."""

    def __init__(self, seq, held, cut):
        self.seq = seq
        self.held = held
        self.cut = cut

    @property
    def last(self):
        return self.seq[-1]

    @property
    def length(self):
        return len(self.seq) - self.cut

    def tokens(self):
        return list(self.seq[self.cut:])

    def span(self, n, tok):
        if len(self.seq) + 1 < n:
            return None
        return self.seq[len(self.seq) + 1 - n:] + (tok,)

    def grow(self, n, tok):
        return Path(self.seq + (tok,), None, self.cut)

    def owns(self, n, span):
        seq = self.seq
        for i in range(len(seq) - n + 1):
            if seq[i:i + n] == span:
                return True
        return False


def root(prompt, n):
    seq = tuple(prompt)
    return Path(seq, None, len(seq))


class Lent:
    """One count per span, kept up to date as members come and go."""

    def __init__(self):
        self.tally = {}

    def take(self, path, n):
        for span in (path.seq[i:i + n] for i in range(len(path.seq) - n + 1)):
            self.tally[span] = self.tally.get(span, 0) + 1

    def give(self, path, n):
        for span in (path.seq[i:i + n] for i in range(len(path.seq) - n + 1)):
            left = self.tally[span] - 1
            if left:
                self.tally[span] = left
            else:
                del self.tally[span]

    def has(self, span):
        return span in self.tally
