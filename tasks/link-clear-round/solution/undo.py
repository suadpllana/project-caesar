"""Walking a change back.

Every effect goes down here as it is applied, with the value it replaced, and comes back in
reverse so that a row taken out after its column was written is restored before that write is
undone, and a row whose key moved is back under the key the later marks name. The matcher is
walked back through the same calls the applying side made, because a stopped change has to
leave nothing behind for the next one to find.
"""


class Log:
    __slots__ = ("marks",)

    def __init__(self):
        self.marks = []

    def gone(self, tab, row):
        self.marks.append(("row", tab, list(row), 0))

    def wrote(self, tab, key, ci, old):
        self.marks.append(("val", tab, key, ci, old))

    def rekeyed(self, tab, old, new):
        self.marks.append(("key", tab, old, new))


def back(work, log):
    st = work.st
    for mark in reversed(log.marks):
        if mark[0] == "row":
            _kind, tab, row, _pad = mark
            st.back(tab, row)
            work.find.add(tab, row)
        elif mark[0] == "val":
            _kind, tab, key, ci, old = mark
            now = st.get(tab, key)[ci]
            st.set(tab, key, ci, old)
            work.find.wrote(tab, key, ci, now, old)
        else:
            _kind, tab, old, new = mark
            work.find.gone(tab, st.get(tab, new))
            st.rekey(tab, new, old)
            work.find.add(tab, st.get(tab, old))
    log.marks = []
