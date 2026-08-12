class Meter:
    def __init__(self):
        self.reads = 0
        self.draws = 0
        self.pos = 0
        self.upd = 0
        self.loads = 0
        self.saves = 0

    def as_map(self):
        return {
            "reads": self.reads,
            "draws": self.draws,
            "pos": self.pos,
            "upd": self.upd,
            "loads": self.loads,
            "saves": self.saves,
        }
