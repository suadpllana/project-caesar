class Out(object):
    def __init__(self):
        self.lines = []

    def page(self, s, ids):
        parts = ["pg", str(s)]
        for i in ids:
            parts.append(str(i))
        self.lines.append(" ".join(parts))

    def report(self, rows, total):
        for s, d, o, u in rows:
            self.lines.append("sc %d %d %d %d" % (s, d, o, u))
        self.lines.append("tot %d" % total)
