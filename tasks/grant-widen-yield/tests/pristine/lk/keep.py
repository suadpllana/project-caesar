from lk import mode


class Due:
    __slots__ = ("mine", "seq")

    def __init__(self):
        self.mine = {}
        self.seq = []

    def owed(self, t, res):
        row = self.mine.get(t)
        return row.get(res) if row else None

    def held(self, t):
        return list(self.mine.get(t, ()))

    def claim(self, t, res, m):
        row = self.mine.setdefault(t, {})
        was = row.get(res)
        row[res] = mode.sup(was, m)
        if was is None:
            self.seq.append((t, res))

    def drop(self, t, res):
        row = self.mine.get(t)
        if not row or res not in row:
            return
        row.pop(res)
        self.seq = [c for c in self.seq if c != (t, res)]

    def under(self, t, res):
        row = self.mine.get(t, {})
        stem = res + "."
        return [r for r in row if r == res or r.startswith(stem)]

    def forget(self, t):
        for res in list(self.mine.get(t, ())):
            self.drop(t, res)
        self.mine.pop(t, None)


def settle(book, due, ages, out, take):
    for t, res in list(due.seq):
        m = due.owed(t, res)
        if m is None:
            continue
        take(book, due, ages, t, res, m, out, False)
