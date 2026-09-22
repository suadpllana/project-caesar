class Tab(object):
    def __init__(self, log):
        self.go = []
        self.ok = []
        self.sig = {}
        self.ch = {}
        for pos, (ev, args) in enumerate(log):
            if ev == "go":
                self.go.append((pos, args[1]))
            elif ev == "ok":
                self.ok.append((pos, int(args[2])))
            elif ev == "sig":
                self.sig.setdefault(args[0], []).append((pos, int(args[1])))
            elif ev == "ch":
                self.ch.setdefault(args[0], []).append((pos, int(args[1])))
        self.ga = 0
        self.oa = 0

    def slot(self, kind, i):
        if self.ga >= len(self.go):
            return None
        got = self.go[self.ga]
        self.ga += 1
        return got

    def answer(self, kind, name, j):
        if self.oa >= len(self.ok):
            return None
        got = self.ok[self.oa]
        self.oa += 1
        return got

    def signal(self, tag, j):
        row = self.sig.get(tag)
        if row is None or j >= len(row):
            return None
        return row[j]

    def choice(self, key, j):
        row = self.ch.get(key)
        if row is None or j >= len(row):
            return None
        return row[j]
