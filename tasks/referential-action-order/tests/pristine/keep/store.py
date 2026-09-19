from .spec import Bad


class Store:
    __slots__ = ("tabs", "rows")

    def __init__(self, tabs):
        self.tabs = tabs
        self.rows = {name: {} for name in tabs}

    def has(self, tab, key):
        return key in self.rows[tab]

    def get(self, tab, key):
        return self.rows[tab][key]

    def held(self, tab):
        return self.rows[tab]

    def add(self, tab, vals):
        here = self.rows[tab]
        if vals[0] in here:
            raise Bad("%s already holds key %d" % (tab, vals[0]))
        here[vals[0]] = list(vals)

    def take(self, tab, key):
        return self.rows[tab].pop(key)

    def back(self, tab, vals):
        self.rows[tab][vals[0]] = list(vals)

    def set(self, tab, key, ci, val):
        self.rows[tab][key][ci] = val

    def rekey(self, tab, key, new):
        row = self.rows[tab].pop(key)
        row[0] = new
        self.rows[tab][new] = row
