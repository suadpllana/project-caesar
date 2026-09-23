"""One multiprocessor's issue rotation.

Each cycle the multiprocessor issues from the first ready block in slot order after the slot
that issued last, wrapping round. A spinning block is ready, and so is a block in the middle
of a sum: every turn it gets is one attempt or one line, so it keeps its place in the rotation
and delays everyone behind it.
"""


class Turn:
    def __init__(self, k):
        self.k = k
        self.last = k - 1

    def pick(self, row, t):
        k = self.k
        for i in range(1, k + 1):
            j = (self.last + i) % k
            b = row[j]
            if b is not None and b.end is None and b.busy <= t:
                self.last = j
                return b
        return None

    def queue(self, row, t):
        """The blocks ready at t, in the order they will issue from t while none joins or leaves."""
        k, out = self.k, []
        for i in range(1, k + 1):
            b = row[(self.last + i) % k]
            if b is not None and b.end is None and b.busy <= t:
                out.append(b)
        return out
