"""The live side, and what the history has left over when the run is done.

The boundary is not a test any one command makes. It opens when the whole run comes to a
stop: no branch able to move and no branch waiting for anything the history recorded. From
that point nothing looks at the history for a command again, which is what leaves recorded
commands unmatched and turns a run that computed a perfectly good value into a failure.

`hit` is a set of history positions rather than a count, because the leftover the run has to
name is the earliest recorded command nobody matched, and after the boundary opens the
unmatched ones are not a suffix of anything.
"""


class Edge(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}
        self.on = False
        self.hit = set()

    def slot(self, kind):
        i = self.n.get(kind, 0)
        self.n[kind] = i + 1
        if self.on:
            return i, None
        return i, self.tab.slot(kind, i)

    def cross(self):
        self.on = True

    def live(self):
        return self.on

    def used(self, pos):
        self.hit.add(pos)

    def leftover(self):
        for pos, kind, at in self.tab.issued():
            if pos not in self.hit:
                return kind, at
        return None
