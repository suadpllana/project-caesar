"""Variant: every write to the store goes through one setter, which keeps the lookup true.

The reference keeps the store and the lookup apart and calls the lookup by hand at each of the
four places a row changes. This one puts the store behind the lookup, so a change to a row is
one call and the remembered slot for the walk-back falls out of the same call.
"""


class Find:
    __slots__ = ("st", "cols", "by", "saved")

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
        self.saved = None

    def kids(self, link, keys):
        by = self.by[(link.kid, link.ci)]
        got = set()
        for key in keys:
            got |= by.get(key, set())
        return sorted(got)

    def slot(self, tab, key):
        return list(self.st.held(tab)[key]) if key in self.st.held(tab) else None

    def put(self, tab, key, row):
        """Give a slot a row, or None to empty it, remembering what was in it."""
        old = self.slot(tab, key)
        if self.saved is not None and (tab, key) not in self.saved:
            self.saved[(tab, key)] = old
        if old is not None:
            for ci in self.cols.get(tab, ()):
                if old[ci] is not None:
                    self.by[(tab, ci)][old[ci]].discard(key)
            self.st.take(tab, key)
        if row is None:
            return
        self.st.back(tab, row)
        for ci in self.cols.get(tab, ()):
            if row[ci] is not None:
                self.by[(tab, ci)].setdefault(row[ci], set()).add(key)
