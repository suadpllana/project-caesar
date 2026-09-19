class Box:
    def __init__(self):
        self.seed = 0
        self.cap = 0
        self.names = []
        self.lens = []
        self.hold = []
        self.pat = []
        self.runs = {}
        self.marks = {}
        self.note = {}
        self.out = []

    def sid(self, name):
        return self.names.index(name)

    def src(self, name, hold, lens):
        self.names.append(name)
        self.hold.append(hold)
        self.lens.append(lens)
        self.note.clear()
