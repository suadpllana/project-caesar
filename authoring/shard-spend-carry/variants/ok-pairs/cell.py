"""A parameter as two parallel lists: where each run starts, and the three numbers it carries.

Written against the brief rather than against the reference, which holds one list of
[count, value, moment, pending] rows instead. Splitting a run here is an insert into both
lists at a bisected position; there it is a rebuild of the row list.
"""
from bisect import bisect_right


class Cell:
    def __init__(self, n):
        self.n = n
        self.live = True
        self.mi = -1
        self.since = 0
        self.warm = False
        self.at = [0]
        self.st = [[0, 0, 0]]

    def _tidy(self):
        at, st = [self.at[0]], [self.st[0]]
        for i in range(1, len(self.at)):
            if self.st[i] != st[-1]:
                at.append(self.at[i])
                st.append(self.st[i])
        self.at, self.st = at, st
        self.warm = any(x[2] for x in st)

    def _cut(self, k):
        i = bisect_right(self.at, k) - 1
        if self.at[i] == k:
            return i
        self.at.insert(i + 1, k)
        self.st.insert(i + 1, list(self.st[i]))
        return i + 1

    def _wide(self, i):
        end = self.at[i + 1] if i + 1 < len(self.at) else self.n
        return end - self.at[i]

    def runs(self, f):
        return [(self._wide(i), self.st[i][f]) for i in range(len(self.at))]

    def take(self, k):
        for x in self.st:
            x[2] += k
        self._tidy()

    def chill(self):
        for x in self.st:
            x[1] = 0
        self._tidy()

    def spend(self, lo, hi, left):
        used = 0
        stop = False
        i = self._cut(lo)
        while i < len(self.at):
            here = self.at[i]
            if here >= hi:
                break
            end = here + self._wide(i)
            if end > hi:
                self._cut(hi)
                end = hi
            g = self.st[i][2]
            if g:
                unit = -g if g < 0 else g
                room = (left - used) // unit
                span = end - here
                if room < span:
                    if room:
                        self._cut(here + room)
                    stop = True
                    span = room
                if span:
                    used += span * unit
                    x = self.st[i]
                    x[1] += g
                    x[0] -= x[1]
                    x[2] = 0
                if stop:
                    break
            i += 1
        self._tidy()
        return used, stop

    def keep(self):
        return [(self._wide(i), self.st[i][0], self.st[i][1]) for i in range(len(self.at))]

    def put(self, runs):
        edge, run = [], 0
        for c, _v, _m in runs:
            run += c
            edge.append(run)
        for k in edge[:-1]:
            self._cut(k)
        i, run = 0, 0
        for c, v, m in runs:
            end = run + c
            while i < len(self.at) and self.at[i] < end:
                if self.at[i] >= run:
                    self.st[i][0] = v
                    self.st[i][1] = m
                i += 1
            run = end
        self._tidy()
