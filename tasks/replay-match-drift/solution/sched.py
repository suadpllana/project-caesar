"""Which branch runs next, and the structure the answer forces.

Two queues over one set of branches, and they are not the same order. A branch that can run
without waiting for anything - one just forked, or one the live side released - goes by the
lowest id. A branch that is waiting goes by the position in the history of the line that
releases it, which has nothing to do with its id or with the order it started waiting in.

The waiting side is a heap rather than a scan. That is not a taste: a branch's place in the
queue is a history position, so the queue reorders itself every time a branch parks, and the
run parks once per recorded answer. Looking for the smallest mark by walking the branches is
exactly correct and costs a pass over every branch at every step, which the wide programs
make infeasible.

`idle` holds the branches waiting on something the history never recorded. Nothing can wake
them, and the run reaching that state for every branch at once is what opens the live side.
"""
import heapq


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
        self.marked = []
        self.idle = []

    def open(self, pc):
        made = Branch(len(self.all), pc)
        self.all.append(made)
        heapq.heappush(self.ready, made.bid)
        return made.bid

    def pick(self):
        while self.ready:
            who = self.all[heapq.heappop(self.ready)]
            if who.state == "ready":
                who.state = "running"
                return who
        while self.marked:
            _mark, bid = heapq.heappop(self.marked)
            who = self.all[bid]
            if who.state == "parked":
                who.state = "running"
                return who
        return None

    def park(self, who, mark):
        who.state = "parked"
        if mark is None:
            self.idle.append(who.bid)
        else:
            heapq.heappush(self.marked, (mark, who.bid))

    def close(self, who):
        who.state = "ended"

    def release(self):
        for bid in sorted(self.idle):
            who = self.all[bid]
            if who.state == "parked":
                who.state = "ready"
                heapq.heappush(self.ready, bid)
        self.idle = []
