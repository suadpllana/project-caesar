class Hold(object):
    def __init__(self):
        self.q = {}

    def add(self, bid, rec):
        self.q.setdefault(bid, []).append(rec)

    def first(self, bid):
        row = self.q.get(bid)
        if not row:
            return None
        return row[-1]

    def drop(self, bid, rec):
        row = self.q.get(bid)
        if not row:
            return
        for at in range(len(row)):
            if row[at] is rec:
                row.pop(at)
                return
