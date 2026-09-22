class Store:
    def __init__(self, script):
        self.script = script
        self.tabs = {t.name: t for t in script.tabs}
        self.data = {t.name: {} for t in script.tabs}

    def add(self, tab, rid, vals):
        self.data[tab][rid] = list(vals)

    def has(self, tab, rid):
        return rid in self.data[tab]

    def get(self, tab, rid):
        return self.data[tab][rid]

    def ids(self, tab):
        return sorted(self.data[tab])

    def drop(self, tab, rid):
        del self.data[tab][rid]

    def put(self, tab, rid, col, val):
        self.data[tab][rid][col] = val
