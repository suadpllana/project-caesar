"""The commands a branch has issued and not yet taken the result of.

One list per branch, in issue order, because a take reaches for the earliest of them and a
branch only ever takes its own.
"""


class Hold(object):
    def __init__(self):
        self.q = {}

    def add(self, bid, rec):
        self.q.setdefault(bid, []).append(rec)

    def first(self, bid):
        row = self.q.get(bid)
        if not row:
            return None
        return row[0]

    def drop(self, bid, rec):
        row = self.q.get(bid)
        if not row:
            return
        for at in range(len(row)):
            if row[at] is rec:
                row.pop(at)
                return
