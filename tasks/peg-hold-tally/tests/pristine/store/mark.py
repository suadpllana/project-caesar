class Marks:
    def __init__(self):
        self.of = {}

    def add(self, p, v, t):
        self.of[p] = (v, t)

    def cut(self, p):
        self.of.pop(p, None)

    def home(self, p):
        return self.of[p]
