from lnk.book import Book, LINK
from pol import adm, emit, rtn, tear


class Mach(object):
    def __init__(self, plan, sink):
        self.plan = plan
        self.sink = sink
        self.bk = Book(plan.feeds)
        self.st = {}

    def run(self):
        for when in range(self.plan.ticks):
            for op, fd, rows in self.plan.at(when):
                if op == "a":
                    self.arrive(when, fd, rows)
                elif op == "t":
                    self.take(when, fd)
                elif op == "x":
                    self.shut(when, fd)
                elif op == "o":
                    self.reopen(when, fd)
            self.publish(when)
        return self.bk

    def arrive(self, when, fd, rows):
        call = adm.verdict(self.st, self.bk, when, fd, rows)
        if call == "ok":
            self.bk.charge(fd, rows)
            self.bk.stow(when, fd, rows)
        elif call == "late":
            self.bk.bill(rows)
            tear.shed(self.st, self.bk, when, fd, rows)
            self.sink(("late", when, fd, rows))
        elif call == "over":
            self.sink(("over", when, fd, rows))
        else:
            raise ValueError("verdict")

    def take(self, when, fd):
        if not self.bk.up(fd):
            return
        rows = self.bk.draw(fd)
        if rows:
            rtn.took(self.st, self.bk, when, fd, rows)

    def shut(self, when, fd):
        if not self.bk.up(fd):
            return
        rows = self.bk.close(when, fd)
        if rows:
            tear.shed(self.st, self.bk, when, fd, rows)
            self.sink(("drop", when, fd, rows))

    def reopen(self, when, fd):
        if self.bk.up(fd):
            return
        self.bk.arm(fd, when)
        tear.opened(self.st, self.bk, when, fd)

    def publish(self, when):
        want = emit.plan(self.st, self.bk, when)
        for level, kind, value in sorted(set(tuple(row) for row in want)):
            if kind not in ("grant", "pull"):
                raise ValueError("kind")
            self.bk.pub[level] = int(value)
            self.sink((kind, when, level, int(value)))
