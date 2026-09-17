class Led:
    def __init__(self):
        self.lines = {}
        self.stills = {}
        self.out = []
        self.nput = 0

    def mint(self):
        self.nput += 1
        return self.nput
