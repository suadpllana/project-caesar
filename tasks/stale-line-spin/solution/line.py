"""One multiprocessor's cache: at most `cap` lines, dropped in the order they were filled.

A dict keeps insertion order, so the line filled earliest is always the first key. A hit
must not touch that order: the machine replaces by fill order, not by use.
"""


class Lines:
    def __init__(self, cap):
        self.cap = cap
        self.rows = {}

    def get(self, ln):
        return self.rows.get(ln)

    def put(self, ln, row):
        """Fill a line that is not cached, dropping the oldest fill when full."""
        if len(self.rows) >= self.cap:
            del self.rows[next(iter(self.rows))]
        self.rows[ln] = row

    def has(self, ln):
        return ln in self.rows

    def drop(self, ln):
        """Drop a line if it is cached; say whether anything changed."""
        return self.rows.pop(ln, None) is not None

    def wipe(self):
        changed = bool(self.rows)
        self.rows.clear()
        return changed
