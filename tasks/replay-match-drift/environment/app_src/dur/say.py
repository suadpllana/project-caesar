class Say(object):
    def __init__(self):
        self.lines = []

    def live(self):
        self.lines.append("live")

    def fork(self, bid, made):
        self.lines.append("%d fork %d" % (bid, made))

    def go(self, bid, kind, idx, name):
        self.lines.append("%d go %s %d %s" % (bid, kind, idx, name))

    def ok(self, bid, kind, idx, value):
        self.lines.append("%d ok %s %d %d" % (bid, kind, idx, value))

    def sig(self, bid, tag, value):
        self.lines.append("%d sig %s %d" % (bid, tag, value))

    def ver(self, bid, key, value):
        self.lines.append("%d ver %s %d" % (bid, key, value))

    def end(self, bid, value):
        self.lines.append("%d end %d" % (bid, value))

    def fin(self, value):
        self.lines.append("fin %d" % value)
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
