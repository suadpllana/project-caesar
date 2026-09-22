class Branch(object):
    __slots__ = ("bid", "pc", "acc", "due", "state")

    def __init__(self, bid, pc):
        self.bid = bid
        self.pc = pc
        self.acc = 0
        self.due = None
        self.state = "ready"


class Sched(object):
    def __init__(self):
        self.all = []
        self.ready = []
        self.parked = []

    def open(self, pc):
        made = Branch(len(self.all), pc)
        self.all.append(made)
        self.ready.append(made.bid)
        return made.bid

    def pick(self):
        best = None
        for bid, mark in self.parked:
            if self.all[bid].state != "parked" or mark is None:
                continue
            if best is None or mark < best[1]:
                best = (bid, mark)
        if best is not None:
            self.parked = [row for row in self.parked if row[0] != best[0]]
            who = self.all[best[0]]
            who.state = "running"
            return who
        while self.ready:
            who = self.all[self.ready.pop(0)]
            if who.state == "ready":
                who.state = "running"
                return who
        return None

    def park(self, who, mark):
        who.state = "parked"
        self.parked.append((who.bid, mark))

    def close(self, who):
        who.state = "ended"

    def release(self):
        for bid, _mark in reversed(self.parked):
            who = self.all[bid]
            if who.state == "parked":
                who.state = "ready"
                self.ready.append(bid)
        self.parked = []
