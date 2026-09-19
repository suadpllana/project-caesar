class Track:
    __slots__ = ("wl", "place", "pending")

    def __init__(self, n):
        self.wl = [() for _ in range(n)]
        self.place = [[] for _ in range(n)]
        self.pending = []

    def take(self):
        held = self.pending
        self.pending = []
        return held

    def defer(self, token, out):
        self.pending.append(token)
        out.line("def %d" % token)
