"""Variant: every row is copied the first time a change touches it, and put back as it was."""


class Log:
    __slots__ = ("seen",)

    def __init__(self):
        self.seen = {}

    def touch(self, work, tab, key):
        if (tab, key) in self.seen:
            return
        self.seen[(tab, key)] = list(work.st.get(tab, key)) if work.st.has(tab, key) else None


def back(work, log):
    for (tab, key), row in log.seen.items():
        if work.st.has(tab, key):
            work.find.gone(tab, work.st.get(tab, key))
            work.st.take(tab, key)
        if row is not None:
            work.st.back(tab, row)
            work.find.add(tab, row)
    log.seen = {}
