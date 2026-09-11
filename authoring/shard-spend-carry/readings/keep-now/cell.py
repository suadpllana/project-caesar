"""Per-slot state of one parameter, held as runs.

A rank stops at the first slot it cannot afford, so an application covers a prefix of a
rank's slice and not a parameter. Two slots of the same parameter therefore diverge, and
they diverge only where a stop or a shard boundary once cut them - which is why the state
is a short list of runs of identical slots rather than one number per parameter, and why
the cuts outlive the boundaries that made them.

A row is [count, value, moment, pending]. Adjacent rows that agree in all three numbers are
folded back together, so a parameter that has never been cut stays one row.
"""


def fold(rows):
    out = []
    for x in rows:
        if x[0] == 0:
            continue
        if out:
            q = out[-1]
            if q[1] == x[1] and q[2] == x[2] and q[3] == x[3]:
                q[0] += x[0]
                continue
        out.append(x)
    return out


class Cell:
    def __init__(self, n):
        self.n = n
        self.live = True
        self.mi = -1
        self.since = 0
        self.warm = False
        self.rows = [[n, 0, 0, 0]]

    def runs(self, f):
        return [(x[0], x[1 + f]) for x in self.rows]

    def take(self, k):
        for x in self.rows:
            x[3] += k
        self.rows = fold(self.rows)
        self.warm = any(x[3] for x in self.rows)

    def chill(self):
        for x in self.rows:
            x[2] = 0
        self.rows = fold(self.rows)

    def spend(self, lo, hi, left):
        """Apply the pending gradients of slots [lo,hi) in order under `left` budget.

        Returns what was spent and whether the rank was stopped. A slot with nothing
        pending costs nothing and is passed over untouched; otherwise it costs the size of
        its pending gradient and is applied only while the running total stays within the
        budget. Inside a run every slot costs the same, so the number of affordable slots
        is one division rather than a walk.
        """
        out = []
        at = used = 0
        stop = warm = False
        for x in self.rows:
            c, v, m, g = x
            s = at
            at = s + c
            if g == 0 or stop or at <= lo or s >= hi:
                out.append(x)
                warm = warm or g != 0
                continue
            head = lo - s if lo > s else 0
            tail = c - (at - hi) if at > hi else c
            cost = g if g > 0 else -g
            k = (left - used) // cost
            span = tail - head
            if k >= span:
                k = span
            else:
                stop = True
            if k <= 0:
                out.append(x)
                warm = True
                continue
            used += k * cost
            nm = m + g
            if head:
                out.append([head, v, m, g])
                warm = True
            out.append([k, v - nm, nm, 0])
            if head + k < c:
                out.append([c - head - k, v, m, g])
                warm = True
        self.rows = fold(out)
        self.warm = warm
        return used, stop

    def keep(self):
        return [(x[0], x[1], x[2]) for x in self.rows]

    def put(self, runs):
        """Lay restored value/moment runs over this parameter, keeping what is pending."""
        out = []
        i = 0
        left = self.rows[0][0]
        for c, v, m in runs:
            need = c
            while need:
                while left == 0:
                    i += 1
                    left = self.rows[i][0]
                k = need if need < left else left
                out.append([k, v, m, self.rows[i][3]])
                need -= k
                left -= k
        self.rows = fold(out)
        self.warm = any(x[3] for x in self.rows)
