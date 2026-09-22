from led import hold
from led import take


class Txn:
    def __init__(self, num):
        self.num = num
        self.taken = take.Taken()
        self.held = hold.Held()
        self.ents = []
        self.marks = []
        self.wrote = set()

    def see(self, store, keys):
        fresh, steps = self.taken.see(store, keys)
        self.held.start(self.taken, fresh)
        for k, step in steps:
            self.held.moved(k, step)

    def shift(self, steps):
        for k, step in steps:
            self.held.moved(k, step)

    def note(self, ent):
        self.ents.append(ent)

    def sets(self, k, ent):
        self.ents.append(ent)
        self.wrote.add(k)

    def mark(self):
        self.marks.append((len(self.ents), self.held.save(self.taken), set(self.wrote)))
        self.ents.append(("m",))

    def cut(self):
        if self.marks:
            back, saved, wrote = self.marks.pop()
            del self.ents[back:]
            self.wrote = wrote
        else:
            self.ents = []
            saved = {}
            self.wrote = set()
        self.held.back(saved, self.taken, self.taken.keys())
