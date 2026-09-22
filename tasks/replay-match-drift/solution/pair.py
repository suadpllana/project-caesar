"""Binding an answer to a command, at the moment the command is issued.

A replayed command takes the next recorded answer of its kind and name; the counter is on
that pair, not on the kind, which is why two commands of one kind that were answered in
the other order still get their own values.

A live command takes the next value the run file offers and is treated as answered after
every recorded one, in the order the live commands were issued. Binding at issue rather
than at take is what makes the race rule cheap: the position an answer arrived at is
already on the record by the time anything competes over it.
"""

AFTER = 1 << 30


class Rec(object):
    def __init__(self, kind, idx, value, pos):
        self.kind = kind
        self.idx = idx
        self.value = value
        self.pos = pos


class Pair(object):
    def __init__(self, tab, feed):
        self.tab = tab
        self.feed = feed
        self.at = 0
        self.n = {}
        self.late = 0

    def bind(self, kind, name, idx, replayed):
        if replayed:
            key = (kind, name)
            j = self.n.get(key, 0)
            self.n[key] = j + 1
            found = self.tab.answer(kind, name, j)
            if found is None:
                return Rec(kind, idx, None, None)
            return Rec(kind, idx, found[1], found[0])
        value = self.feed[self.at] if self.at < len(self.feed) else 0
        self.at += 1
        self.late += 1
        return Rec(kind, idx, value, AFTER + self.late)
