from opt import keep, lay


class Reg:
    def __init__(self):
        self.par = {}
        self.order = []
        self.ws = 1
        self.bud = 0
        self.clock = 0
        self.out = []
        lay.init(self)
        keep.init(self)
