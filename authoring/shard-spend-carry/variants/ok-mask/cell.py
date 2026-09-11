"""A parameter as rows that record where each run ends rather than how long it is."""


def fold(rows):
    out = []
    for x in rows:
        if out:
            q = out[-1]
            if q[0] == x[0]:
                continue
            if q[1] == x[1] and q[2] == x[2] and q[3] == x[3]:
                q[0] = x[0]
                continue
        elif x[0] == 0:
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
        out = []
        at = 0
        for end, v, m, _g in self.rows:
            out.append((end - at, (v, m)[f]))
            at = end
        return out

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
        out = []
        at = used = 0
        stop = warm = False
        for x in self.rows:
            end, v, m, g = x
            start, at = at, end
            if g == 0 or stop or end <= lo or start >= hi:
                out.append(x)
                warm = warm or g != 0
                continue
            head = lo if lo > start else start
            tail = hi if hi < end else end
            unit = g if g > 0 else -g
            room = (left - used) // unit
            span = tail - head
            if room < span:
                stop = True
                span = room
            if span <= 0:
                out.append(x)
                warm = True
                continue
            used += span * unit
            nm = m + g
            if head > start:
                out.append([head, v, m, g])
                warm = True
            out.append([head + span, v - nm, nm, 0])
            if head + span < end:
                out.append([end, v, m, g])
                warm = True
        self.rows = fold(out)
        self.warm = warm
        return used, stop

    def keep(self):
        out = []
        at = 0
        for end, v, m, _g in self.rows:
            out.append((end - at, v, m))
            at = end
        return out

    def put(self, runs):
        out = []
        at = 0
        old = list(self.rows)
        i = 0
        for c, v, m in runs:
            left = c
            while left:
                while old[i][0] <= at:
                    i += 1
                take = old[i][0] - at
                if take > left:
                    take = left
                out.append([at + take, v, m, old[i][3]])
                at += take
                left -= take
        self.rows = fold(out)
        self.warm = any(x[3] for x in self.rows)
