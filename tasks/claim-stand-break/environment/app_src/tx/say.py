class Out:
    __slots__ = ("lines",)

    def __init__(self):
        self.lines = []

    def line(self, text):
        self.lines.append(text)


def _rows(got):
    if not got:
        return "-"
    return " ".join("%d:%d" % (key, val) for key, val in got)


def read(out, tid, key, val):
    out.line("read %d %d %s" % (tid, key, "-" if val is None else val))


def span(out, tid, got):
    out.line("span %d %s" % (tid, _rows(got)))


def dead(out, tid, i):
    out.line("dead %d %d" % (tid, i))


def done(out, tid, i):
    out.line("seal %d %s" % (tid, "ok" if i is None else "no %d" % i))


def look(out, got):
    out.line("look %s" % _rows(got))
