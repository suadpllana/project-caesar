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
        self.held.start(self.taken.see(store, keys))

    def note(self, ent):
        self.ents.append(ent)

    def sets(self, k, ent):
        self.ents.append(ent)
        self.wrote.add(k)

    def mark(self):
        self.marks.append((len(self.ents), self.held.save(), set(self.wrote)))
        self.ents.append(("m",))

    def cut(self):
        if self.marks:
            back, form, wrote = self.marks.pop()
            del self.ents[back:]
            self.wrote = wrote
        else:
            self.ents = []
            form = {}
            self.wrote = set()
        self.held.back(form, self.taken.keys())
