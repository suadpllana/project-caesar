class Out:
    __slots__ = ("lines",)

    def __init__(self):
        self.lines = []

    def frame(self, i, off, gid, band, w0, w1, key, gap, m, p):
        self.lines.append(
            "f %d s %d g %d b %d w %d %d h %s %d m %d p %d"
            % (i, off, gid, band, w0, w1, key, gap, m, p)
        )

    def end(self, off, total, m):
        self.lines.append("end s %d t %d m %d" % (off, total, m))
