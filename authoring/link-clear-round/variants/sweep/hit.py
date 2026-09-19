"""Variant: the lookup is kept per link rather than per column."""


class Find:
    __slots__ = ("st", "by", "on")

    def __init__(self, st, links):
        self.st = st
        self.by = [dict() for _ in links]
        self.on = {}
        for li, ln in enumerate(links):
            self.on.setdefault(ln.kid, {}).setdefault(ln.ci, []).append(li)

    def kids(self, li, keys):
        by = self.by[li]
        got = set()
        for key in keys:
            got |= by.get(key, set())
        return sorted(got)

    def add(self, tab, row):
        for ci, lis in self.on.get(tab, {}).items():
            val = row[ci]
            if val is None:
                continue
            for li in lis:
                self.by[li].setdefault(val, set()).add(row[0])

    def gone(self, tab, row):
        for ci, lis in self.on.get(tab, {}).items():
            val = row[ci]
            if val is None:
                continue
            for li in lis:
                self.by[li][val].discard(row[0])

    def wrote(self, tab, key, ci, old, new):
        for li in self.on.get(tab, {}).get(ci, ()):
            if old is not None:
                self.by[li][old].discard(key)
            if new is not None:
                self.by[li].setdefault(new, set()).add(key)
