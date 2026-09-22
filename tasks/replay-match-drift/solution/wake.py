"""What a branch is waiting for, and the mark that puts it in the queue.

A branch waiting for an answer is released by the line that carries it, so its mark is that
line's position, which was settled when the command was bound. A branch waiting for a signal
has to claim one at the moment it parks: two branches waiting on the same tag take different
lines, and which of them takes the earlier one depends on which parked first, which depends
on the schedule the marks themselves produce.

A branch waiting for something the history never recorded gets no mark at all. It is that
case, holding for every branch at once, that opens the live side.
"""


class Wake(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}
        self.claim = {}

    def mark(self, bid, due):
        kind, payload = due
        if kind == "ok":
            return payload.pos
        at = self.n.get(payload, 0)
        found = self.tab.signal(payload, at)
        if found is None:
            return None
        self.n[payload] = at + 1
        self.claim[bid] = found[1]
        return found[0]

    def take(self, bid, tag, pair):
        if bid in self.claim:
            return self.claim.pop(bid)
        at = self.n.get(tag, 0)
        found = self.tab.signal(tag, at)
        if found is None:
            return pair.spare()
        self.n[tag] = at + 1
        return found[1]
