class Say(object):
    def __init__(self):
        self.lines = []

    def live(self):
        self.lines.append("live")

    def go(self, kind, idx, name):
        self.lines.append("go %s %d %s" % (kind, idx, name))

    def ok(self, kind, idx, value):
        self.lines.append("ok %s %d %d" % (kind, idx, value))

    def sig(self, tag, value):
        self.lines.append("sig %s %d" % (tag, value))

    def ver(self, key, value):
        self.lines.append("ver %s %d" % (key, value))

    def fin(self, value):
        self.lines.append("fin %d" % value)
        return self.lines

    def hold(self, kind, idx):
        self.lines.append("hold %s %d" % (kind, idx))
        return self.lines

    def holdsig(self, tag):
        self.lines.append("hold sig %s" % tag)
        return self.lines

    def holdnone(self):
        self.lines.append("hold none")
        return self.lines

    def drift(self, kind, idx, want, got):
        self.lines.append("drift %s %d %s %s" % (kind, idx, want, got))
        return self.lines

    def left(self, kind, idx):
        self.lines.append("drift left %s %d" % (kind, idx))
        return self.lines

    def over(self):
        self.lines.append("over")
        return self.lines
