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
        seq = self.seq + (tok,)
        held = self.held
        if len(seq) >= n:
            held = held | frozenset([seq[len(seq) - n:]])
        return Path(seq, held, self.cut)


def root(prompt, n):
    seq = tuple(prompt)
    held = frozenset(seq[i:i + n] for i in range(len(seq) - n + 1))
    return Path(seq, held, len(seq))


class Lent:
    """One count per span, kept up to date as members come and go."""

    def __init__(self):
        self.tally = {}

    def take(self, path):
        for span in path.held:
            self.tally[span] = self.tally.get(span, 0) + 1

    def give(self, path):
        for span in path.held:
            left = self.tally[span] - 1
            if left:
                self.tally[span] = left
            else:
                del self.tally[span]

    def has(self, span):
        return span in self.tally
