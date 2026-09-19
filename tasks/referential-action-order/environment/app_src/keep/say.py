class Out:
    __slots__ = ("lines",)

    def __init__(self):
        self.lines = []

    def none(self, tab, key):
        self.lines.append("none %s %d" % (tab, key))

    def clash(self, tab, key):
        self.lines.append("clash %s %d" % (tab, key))

    def bar(self, link, tab, key):
        self.lines.append("bar %s %s %d" % (link, tab, key))

    def wait(self, link, tab, key):
        self.lines.append("wait %s %s %d" % (link, tab, key))

    def drop(self, tab, key, link):
        self.lines.append("drop %s %d %s" % (tab, key, link))

    def clear(self, tab, key, col, link):
        self.lines.append("clear %s %d %s %s" % (tab, key, col, link))

    def move(self, tab, key, col, val, link):
        self.lines.append("move %s %d %s %d %s" % (tab, key, col, val, link))
