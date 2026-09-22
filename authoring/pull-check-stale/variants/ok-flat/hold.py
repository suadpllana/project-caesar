class Loop(Exception):
    def __init__(self, chain):
        Exception.__init__(self)
        self.chain = chain


class Stuck(Exception):
    def __init__(self, name):
        Exception.__init__(self)
        self.name = name


class Board:
    def __init__(self, p):
        names = list(p.order)
        self.rec = dict((n, []) for n in names)
        self.fact = dict((n, None) for n in names)
        self.seen = dict((n, -1) for n in names)
        self.ran = dict((n, False) for n in names)

    def open_round(self):
        for n in self.ran:
            self.ran[n] = False

    def wipe(self, n):
        self.rec[n] = []
        self.fact[n] = None
        self.seen[n] = -1
