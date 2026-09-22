"""Variant A: the waiting branches in one list held in order, rather than in a heap."""
import bisect


class Branch(object):
    def __init__(self, bid, pc):
        self.bid = bid
        self.pc = pc
        self.acc = 0
        self.due = None
        self.state = "ready"


class Sched(object):
    def __init__(self):
        self.all = []
        self.free = []
        self.held = []
        self.stuck = []

    def open(self, pc):
        made = Branch(len(self.all), pc)
        self.all.append(made)
        bisect.insort(self.free, made.bid)
        return made.bid

    def pick(self):
        if self.free:
            who = self.all[self.free.pop(0)]
            who.state = "running"
            return who
        if self.held:
            who = self.all[self.held.pop(0)[1]]
            who.state = "running"
            return who
        return None

    def park(self, who, mark):
        who.state = "parked"
        if mark is None:
            self.stuck.append(who.bid)
        else:
            bisect.insort(self.held, (mark, who.bid))

    def close(self, who):
        who.state = "ended"

    def release(self):
        for bid in self.stuck:
            if self.all[bid].state == "parked":
                self.all[bid].state = "ready"
                bisect.insort(self.free, bid)
        self.stuck = []
