class Rec:
    def __init__(self, name):
        self.name = name
        self.needs = []
        self.pubs = []
        self.boots = []
        self.live = False
        self.uses = {}


class Host:
    def __init__(self):
        self.units = {}
        self.seq = {}
        self.holds = {}


def get(h, name):
    r = h.units.get(name)
    if r is None:
        r = Rec(name)
        h.units[name] = r
    return r
