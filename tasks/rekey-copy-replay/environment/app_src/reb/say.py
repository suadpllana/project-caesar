class Say:
    def __init__(self):
        self.lines = []

    def chunk(self, n, cur, mark):
        self.lines.append("chunk %d %d %s" % (n, cur, "none" if mark is None else mark))

    def on(self, k, a, b):
        self.lines.append("on %d %d:%d" % (k, a, b))

    def aside(self, k, a, b):
        self.lines.append("aside %d %d:%d" % (k, a, b))

    def off(self, k, a, b):
        self.lines.append("off %d %d:%d" % (k, a, b))

    def drop(self, k, a, b):
        self.lines.append("drop %d %d:%d" % (k, a, b))

    def same(self, k, a, b):
        self.lines.append("same %d %d:%d" % (k, a, b))

    def miss(self, k):
        self.lines.append("miss %d" % k)

    def entry(self, pos, k, verdict):
        self.lines.append("entry %d %d %s" % (pos, k, verdict))

    def end(self, placed, aside, total):
        self.lines.append("end %d %d %d" % (placed, aside, total))
