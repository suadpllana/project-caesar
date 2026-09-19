"""Per-token state, with the queue as a deque and the refusals as a list."""
import collections


class Track:
    __slots__ = ("wl", "place", "blocked", "gone", "pending")

    def __init__(self, n):
        self.wl = [()] * n
        self.place = {}
        self.blocked = [[] for _ in range(n)]
        self.gone = [False] * n
        self.pending = collections.deque()

    def held(self, tid):
        return self.place.setdefault(tid, [])

    def take(self):
        held = list(self.pending)
        self.pending.clear()
        return held

    def refuse(self, tid, e):
        if e not in self.blocked[tid]:
            self.blocked[tid].append(e)

    def defer(self, tid, last, out):
        if last:
            return
        self.pending.append(tid)
        out.line("def %d" % tid)
