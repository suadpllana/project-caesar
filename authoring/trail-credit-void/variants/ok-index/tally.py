class Sum:
    __slots__ = ("rows",)

    def __init__(self):
        self.rows = []

    def add(self, got, whole):
        self.rows.append((got, whole))


def done(one, book, used, sums, out):
    got = 0
    whole = 0
    for goal in one.goals:
        whole += goal.weight
        if book.held(goal.gid):
            got += goal.weight
    out.line("ep %s %d %d %d" % (one.name, got, whole, used))
    sums.add(got, whole)


def close(sums, out):
    full = sum(1 for got, whole in sums.rows if got == whole)
    out.line("run %d %d %d %d" % (len(sums.rows), full,
                                  sum(got for got, _w in sums.rows),
                                  sum(whole for _g, whole in sums.rows)))
