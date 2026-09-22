class Book:
    __slots__ = ("ents", "nchg", "upto", "dead", "woken", "sleepers", "own")

    def __init__(self, prog):
        self.ents = prog.ents
        self.nchg = prog.nchg
        self.upto = 0
        self.dead = set()
        self.woken = set()
        self.sleepers = []
        self.own = [[] for _ in range(prog.nchg)]
        for i, ent in enumerate(prog.ents):
            self.own[ent.chg].append(i)

    def stands(self, i):
        return self.ents[i].chg not in self.dead

    def active(self, i):
        ent = self.ents[i]
        if ent.chg in self.dead:
            return False
        return ent.guard != "once" or i in self.woken

    def append(self, i):
        self.upto = i + 1
        if self.ents[i].guard == "once":
            self.sleepers.append(i)

    def turn(self, chg, dead):
        if (chg in self.dead) == dead:
            return ()
        if dead:
            self.dead.add(chg)
        else:
            self.dead.discard(chg)
        return self.own[chg]
