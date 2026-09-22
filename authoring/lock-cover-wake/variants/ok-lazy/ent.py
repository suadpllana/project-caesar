import heapq
from collections import Counter, deque

from . import mode


class Item:
    __slots__ = ("tid", "seq", "m", "conv", "cont")

    def __init__(self, tid, seq, m, conv, cont):
        self.tid = tid
        self.seq = seq
        self.m = m
        self.conv = conv
        self.cont = cont


class Ent:
    """Two deques, and the earliest begin waiting here kept as a heap read lazily."""

    __slots__ = ("res", "held", "how", "cq", "nq", "ages", "gen")

    def __init__(self, res):
        self.res = res
        self.held = {}
        self.how = Counter()
        self.cq = deque()
        self.nq = deque()
        self.ages = []
        self.gen = 0

    def give(self, tid, m):
        was = self.held.get(tid)
        if was == m:
            return
        if was is not None:
            self.how[was] -= 1
        self.held[tid] = m
        self.how[m] += 1

    def take(self, tid):
        was = self.held.pop(tid, None)
        if was is not None:
            self.how[was] -= 1

    def hits_but(self, tid, m):
        mine = self.held.get(tid)
        for bad in mode.BAD[m]:
            if self.how[bad] > (1 if mine == bad else 0):
                return True
        return False

    def foes(self, tid, m):
        bad = mode.BAD[m]
        return [k for k, v in self.held.items() if k != tid and v in bad]

    def waiting(self):
        return bool(self.cq) or bool(self.nq)

    def head(self):
        return self.cq[0] if self.cq else self.nq[0]

    def queued(self):
        return list(self.cq) + list(self.nq)

    def push(self, it):
        (self.cq if it.conv else self.nq).append(it)
        heapq.heappush(self.ages, it.seq)
        self.gen += 1

    def pop_head(self):
        it = self.cq.popleft() if self.cq else self.nq.popleft()
        self.gen += 1
        return it

    def drop_wait(self, tid):
        for q in (self.cq, self.nq):
            for it in q:
                if it.tid == tid:
                    q.remove(it)
                    self.gen += 1
                    return it
        return None

    @property
    def old(self):
        """The earliest begin still waiting here; stale heap entries are dropped on the way."""
        live = None
        while self.ages:
            seq = self.ages[0]
            if live is None:
                live = set()
                for q in (self.cq, self.nq):
                    for it in q:
                        live.add(it.seq)
            if seq in live:
                return seq
            heapq.heappop(self.ages)
        return None
