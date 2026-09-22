class Lines:
    def __init__(self, cap):
        self.cap = cap
        self.rows = {}

    def get(self, ln):
        row = self.rows.pop(ln, None)
        if row is not None:
            self.rows[ln] = row
        return row

    def put(self, ln, row):
        if ln not in self.rows and len(self.rows) >= self.cap:
            del self.rows[next(iter(self.rows))]
        self.rows.pop(ln, None)
        self.rows[ln] = row

    def has(self, ln):
        return ln in self.rows
