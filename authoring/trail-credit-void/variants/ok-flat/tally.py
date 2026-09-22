class Sum:
    __slots__ = ("eps", "full", "got", "whole")

    def __init__(self):
        self.eps = 0
        self.full = 0
        self.got = 0
        self.whole = 0

    def add(self, got, whole):
        self.eps += 1
        self.got += got
        self.whole += whole
        if got == whole:
            self.full += 1


def done(one, book, used, sums, out):
    got = sum(goal.weight for goal in one.goals if book.held(goal.gid))
    whole = sum(goal.weight for goal in one.goals)
    out.line("ep %s %d %d %d" % (one.name, got, whole, used))
    sums.add(got, whole)


def close(sums, out):
    out.line("run %d %d %d %d" % (sums.eps, sums.full, sums.got, sums.whole))
