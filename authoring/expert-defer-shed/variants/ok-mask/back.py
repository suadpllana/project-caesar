"""Per-token state, with placements as a pair of parallel lists."""


class Track:
    __slots__ = ("wl", "place", "blocked", "gone", "pending")

    def __init__(self, n):
        self.wl = [()] * n
        self.place = [([], []) for _ in range(n)]
        self.blocked = [set() for _ in range(n)]
        self.gone = [False] * n
        self.pending = []

    def take(self):
        held = self.pending
        self.pending = []
        return held

    def refuse(self, tid, e):
        self.blocked[tid].add(e)

    def defer(self, tid, last, out):
        if last:
            return
        self.pending.append(tid)
        out.line("def %d" % tid)
