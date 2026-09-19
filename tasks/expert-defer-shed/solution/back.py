"""What a token carries through a step, and the queue that survives a microbatch.

Three of these are per token and none of them is a field on anything the service ships: the
experts that have refused it, whether it has already been displaced, and the want list as it
now stands. The queue holds only tokens that lost or never got rank zero, in the order the
losses happened, and it is emptied at the head of the next microbatch. The last microbatch has
no next one, so a loss there is simply held and nothing is printed for it.
"""


class Track:
    __slots__ = ("wl", "place", "blocked", "gone", "pending")

    def __init__(self, n):
        self.wl = [() for _ in range(n)]
        self.place = [[] for _ in range(n)]
        self.blocked = [set() for _ in range(n)]
        self.gone = [False] * n
        self.pending = []

    def take(self):
        held = self.pending
        self.pending = []
        return held

    def refuse(self, token, e):
        self.blocked[token].add(e)

    def defer(self, token, last, out):
        if last:
            return
        self.pending.append(token)
        out.line("def %d" % token)
