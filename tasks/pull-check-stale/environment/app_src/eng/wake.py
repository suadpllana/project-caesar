from eng import mark
from eng.step import run_step


class Loop(Exception):
    def __init__(self, chain):
        Exception.__init__(self)
        self.chain = chain


class Wake:
    def __init__(self, p, keep, board, out):
        self.plan = p
        self.keep = keep
        self.board = board
        self.out = out
        self.path = []

    def open_round(self):
        self.board.open_round()

    def request(self, name):
        self.path = []
        try:
            hold = self.up(name)
        except Loop as exc:
            self.out.loop(exc.chain)
            return
        if hold.dead:
            self.out.err(name, hold.why)
        else:
            self.out.ok(name, hold.value)

    def up(self, name):
        if name in self.path:
            raise Loop(self.path + [name])
        if self.board.settled(name):
            return self.board.get(name)
        self.path.append(name)
        try:
            hold = self.board.get(name)
            if hold.known and self.sound(hold):
                self.board.settle(name)
                return hold
            if hold.dead:
                self.board.forget(name)
            return run_step(self, name)
        finally:
            self.path.pop()

    def sound(self, hold):
        good = True
        for m in hold.rec:
            if mark.is_pull(m):
                other = self.up(m[1])
                if other.dead:
                    if m[2] != "!":
                        good = False
                elif m[2] == "!":
                    good = False
                elif other.value != m[2]:
                    good = False
            elif not mark.flat_holds(m, self.keep):
                good = False
        return good
