class Store:
    def __init__(self, cfg, lk):
        self.n = cfg["nsamp"]
        self.lk = lk

    def raw(self, sid):
        return self.lk.call("row", [sid])

    def snap(self):
        return []

    def rest(self, vec):
        return None
