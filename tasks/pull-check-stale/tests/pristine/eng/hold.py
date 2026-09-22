class Hold:
    def __init__(self, name):
        self.name = name
        self.rec = []
        self.value = None
        self.why = None
        self.dead = False
        self.known = False


class Board:
    def __init__(self, p):
        self.holds = {}
        for name in p.order:
            self.holds[name] = Hold(name)
        self.fresh = set()

    def get(self, name):
        return self.holds[name]

    def open_round(self):
        self.fresh = set()

    def settled(self, name):
        return name in self.fresh

    def settle(self, name):
        self.fresh.add(name)

    def forget(self, name):
        h = self.holds[name]
        h.rec = []
        h.value = None
        h.why = None
        h.dead = False
        h.known = False
