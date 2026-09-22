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

    def rebuilt(self, n):
        seq = self.seq
        out = set()
        for i in range(len(seq) - n + 1):
            out.add(seq[i:i + n])
        return out


def root(prompt, n):
    seq = tuple(prompt)
    return Path(seq, None, len(seq))


class Lent:
    """One count per span, kept up to date as members come and go."""

    def __init__(self):
        self.tally = {}

    def take(self, path, n):
        for span in path.rebuilt(n):
            self.tally[span] = self.tally.get(span, 0) + 1

    def give(self, path, n):
        for span in path.rebuilt(n):
            left = self.tally[span] - 1
            if left:
                self.tally[span] = left
            else:
                del self.tally[span]

    def has(self, span):
        return span in self.tally
