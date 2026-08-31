class Fib:
    __slots__ = ("fid", "pid", "fr", "bl", "inh", "st", "wake", "warm",
                 "pend", "toks", "hold", "home", "fin")

    def __init__(self, fid, pid, ops, inh, home):
        self.fid = fid
        self.pid = pid
        self.fr = [[ops, 0]]
        self.bl = []
        self.inh = inh
        self.st = 0
        self.wake = None
        self.warm = False
        self.pend = None
        self.toks = []
        self.hold = None
        self.home = home
        self.fin = -1

    def deep(self):
        return len(self.fr) > 1
