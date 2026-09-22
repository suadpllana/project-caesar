class Held:
    def __init__(self):
        self.num = {}

    def start(self, taken, keys):
        for k in keys:
            self.num[k] = taken.at(k)

    def at(self, k, taken):
        return self.num[k]

    def put(self, k, n):
        self.num[k] = n

    def add(self, k, n):
        self.num[k] = self.num[k] + n

    def copy(self, k, j):
        self.num[k] = self.num[j]

    def raw(self, k, j, taken):
        self.num[k] = taken.at(j)

    def stick(self, k, v):
        self.num[k] = v

    def redo(self, ents, taken):
        self.num = {}
        for k in taken.keys():
            self.num[k] = taken.at(k)
        for ent in ents:
            kind = ent[0]
            if kind == "p":
                self.num[ent[1]] = ent[2]
            elif kind == "a":
                self.num[ent[1]] = self.num[ent[1]] + ent[2]
            elif kind == "c":
                self.num[ent[1]] = self.num[ent[2]]
            elif kind == "r":
                self.num[ent[1]] = taken.at(ent[2])
            elif kind == "f":
                self.num[ent[1]] = ent[2]
