"""Where replay stops, and what the log has left over when the body is done.

One boundary for the whole run, not one per kind. A command whose own kind has run out of
recorded slots opens it, and from that point nothing consults the log for a slot again -
which is what leaves the other kinds' recorded commands unmatched and turns a run that
computed a perfectly good value into a failure.

`used` is a set of log positions rather than a count, because the leftover the run has to
name is the earliest recorded command the body never issued, and after a boundary crossing
the unmatched ones are not a suffix of anything.
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
            return i, None, False
        found = self.tab.slot(kind, i)
        if found is None:
            self.on = True
            return i, None, True
        return i, found, False

    def live(self):
        return self.on

    def used(self, pos):
        self.hit.add(pos)

    def leftover(self):
        for pos, kind, at in self.tab.issued():
            if pos not in self.hit:
                return kind, at
        return None
