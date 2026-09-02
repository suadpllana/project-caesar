class Log:
    def __init__(self):
        self.rows = []

    def put(self, pn, code, rest):
        self.rows.append("%d %s %s" % (pn, code, rest))

    def text(self):
        return "\n".join(self.rows)
