class Store:
    def __init__(self):
        self.val = {}

    def open(self, wide):
        self.val = {}
        for k in range(wide):
            self.val[k] = 0

    def at(self, k):
        return self.val[k]

    def snap(self):
        return dict(self.val)

    def write(self, keys, held):
        pairs = []
        for k in keys:
            if held[k] != self.val[k]:
                pairs.append((k, held[k]))
        for k, v in pairs:
            self.val[k] = v
        return pairs
