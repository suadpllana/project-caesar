"""Variant B: a heap of waiting branches carrying a sequence number, ready as a plain list."""
import heapq


class Branch(object):
    __slots__ = ("bid", "pc", "acc", "due", "state")

    def __init__(self, bid, pc):
        self.bid, self.pc, self.acc, self.due, self.state = bid, pc, 0, None, "ready"


class Sched(object):
    def __init__(self):
        self.all = []
        self.free = []
        self.wait = []
        self.dark = []
        self.tick = 0

    def open(self, pc):
        made = Branch(len(self.all), pc)
        self.all.append(made)
        heapq.heappush(self.free, made.bid)
        return made.bid

    def pick(self):
        if self.free:
            who = self.all[heapq.heappop(self.free)]
            who.state = "running"
            return who
        if self.wait:
            who = self.all[heapq.heappop(self.wait)[2]]
            who.state = "running"
            return who
        return None

    def park(self, who, mark):
        who.state = "parked"
        if mark is None:
            self.dark.append(who.bid)
            return
        self.tick += 1
        heapq.heappush(self.wait, (mark, self.tick, who.bid))

    def close(self, who):
        who.state = "ended"

    def release(self):
        for bid in self.dark:
            if self.all[bid].state == "parked":
                self.all[bid].state = "ready"
                heapq.heappush(self.free, bid)
        self.dark = []
