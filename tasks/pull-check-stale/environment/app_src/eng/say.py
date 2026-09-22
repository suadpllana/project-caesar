class Say:
    def __init__(self):
        self.lines = []

    def round(self, n):
        self.lines.append("round %d" % n)

    def run(self, name):
        self.lines.append("run %s" % name)

    def ok(self, name, value):
        self.lines.append("ok %s %s" % (name, value))

    def err(self, name, why):
        self.lines.append("err %s %s" % (name, why))

    def loop(self, chain):
        self.lines.append("loop %s" % " ".join(chain))

    def stuck(self, name):
        self.lines.append("stuck %s" % name)

    def text(self):
        return "\n".join(self.lines)
