"""One multiprocessor's issue rotation.

Each cycle the multiprocessor issues from the first ready block in slot order after the slot
that issued last, wrapping round. A spinning block is ready: every turn it gets is one
attempt, so spinners keep their place in the rotation and delay everyone behind them.
"""


class Turn:
    def __init__(self, k):
        self.k = k
        self.last = k - 1

    @staticmethod
    def ready(b, t):
        return b is not None and b.end is None and b.busy <= t

    def pick(self, row, t):
        k = self.k
        for i in range(1, k + 1):
            j = (self.last + i) % k
            b = row[j]
            if b is not None and b.end is None and b.busy <= t:
                self.last = j
                return b
        return None

    def skip(self, row, t, d):
        """Account for d cycles in which the ready blocks only took failing, idle turns."""
        ready = [j for j in range(self.k) if self.ready(row[j], t)]
        if ready:
            order = sorted(ready, key=lambda j: (j - self.last - 1) % self.k)
            self.last = order[(d - 1) % len(order)]
