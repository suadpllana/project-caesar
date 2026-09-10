class Trace:
    def __init__(self):
        self.lines = []

    def give(self, t, k, m):
        self.lines.append("give %s %s %s" % (t, k, m))

    def wait(self, t, k, m):
        self.lines.append("wait %s %s %s" % (t, k, m))

    def free(self, t, k, m):
        self.lines.append("free %s %s %s" % (t, k, m))

    def cut(self, t):
        self.lines.append("cut %s" % t)

    def done(self, t):
        self.lines.append("done %s" % t)

    def text(self):
        return "\n".join(self.lines)
