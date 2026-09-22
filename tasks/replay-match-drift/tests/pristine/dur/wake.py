class Wake(object):
    def __init__(self, tab):
        self.tab = tab
        self.n = {}

    def mark(self, bid, due):
        kind, payload = due
        if kind == "ok":
            return payload.pos
        found = self.tab.signal(payload, self.n.get(payload, 0))
        if found is None:
            return None
        return found[0]

    def take(self, bid, tag, pair):
        at = self.n.get(tag, 0)
        found = self.tab.signal(tag, at)
        if found is None:
            return pair.spare()
        self.n[tag] = at + 1
        return found[1]
