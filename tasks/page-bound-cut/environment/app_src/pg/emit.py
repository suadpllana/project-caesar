class Out:
    def __init__(self):
        self.lines = []

    def add(self, key, pid):
        self.lines.append("add %s p%d" % (key, pid))

    def dup(self, key):
        self.lines.append("dup %s" % key)

    def rm(self, key, pid):
        self.lines.append("rm %s p%d" % (key, pid))

    def none(self, key):
        self.lines.append("none %s" % key)

    def bound(self, pid, idx, sep):
        self.lines.append("bound p%d %d %s" % (pid, idx, sep))

    def cut(self, left, right, pos, sep):
        self.lines.append("cut p%d p%d %d %s" % (left, right, pos, sep))

    def gone(self, pid):
        self.lines.append("gone p%d" % pid)

    def join(self, left, right):
        self.lines.append("join p%d p%d" % (left, right))

    def root(self, pid):
        self.lines.append("root p%d" % pid)

    def fold(self, pid):
        self.lines.append("fold p%d" % pid)
