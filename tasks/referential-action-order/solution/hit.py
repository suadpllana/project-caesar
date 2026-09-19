"""Which rows point at a set of keys.

A scan of the child table answers this exactly and is what the shipped service does. It is
also why the wide programs do not finish: forty thousand rows behind three thousand changes
is a hundred million row reads. The index here is sound because of one fact the contract
guarantees - a column under a link changes only through an effect a change applies - so every
write already passes through this file, and an undo passes back through it the same way.
"""


class Find:
    __slots__ = ("st", "cols", "by")

    def __init__(self, st, links):
        self.st = st
        self.cols = {}
        self.by = {}
        watch = {}
        for ln in links:
            watch.setdefault(ln.kid, set()).add(ln.ci)
            self.by[(ln.kid, ln.ci)] = {}
        for tab, cis in watch.items():
            self.cols[tab] = tuple(sorted(cis))

    def kids(self, link, keys):
        by = self.by[(link.kid, link.ci)]
        got = set()
        for key in keys:
            here = by.get(key)
            if here:
                got |= here
        return sorted(got)

    def add(self, tab, row):
        for ci in self.cols.get(tab, ()):
            val = row[ci]
            if val is not None:
                self.by[(tab, ci)].setdefault(val, set()).add(row[0])

    def gone(self, tab, row):
        for ci in self.cols.get(tab, ()):
            val = row[ci]
            if val is not None:
                self.by[(tab, ci)][val].discard(row[0])

    def wrote(self, tab, key, ci, old, new):
        if ci not in self.cols.get(tab, ()):
            return
        by = self.by[(tab, ci)]
        if old is not None:
            by[old].discard(key)
        if new is not None:
            by.setdefault(new, set()).add(key)
