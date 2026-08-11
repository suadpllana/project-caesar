class Sch:
    def __init__(self, cfg):
        self.mb = int(cfg["max_batch"])
        self.wait = []
        self.run = []
        self.eng = None
        self.n_sync = 0

    def add(self, s):
        self.wait.append(s)

    def all(self):
        return list(self.run) + list(self.wait)

    def busy(self):
        return bool(self.run or self.wait)

    def pick(self):
        while self.wait and len(self.run) < self.mb:
            self.run.append(self.wait.pop(0))
        return list(self.run)

    def victim(self, cur):
        for s in reversed(self.run):
            if s is not cur:
                return s
        return None

    def requeue(self, s):
        if s in self.run:
            self.run.remove(s)
        self.wait.insert(0, s)

    def finish(self, s):
        if s in self.run:
            self.run.remove(s)
        if s in self.wait:
            self.wait.remove(s)

    def on_sync(self, ps):
        self.n_sync += 1
        for s in self.run:
            s.sync_n = self.n_sync
        for s in self.wait:
            s.sync_n = self.n_sync
