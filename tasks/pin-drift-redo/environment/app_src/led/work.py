from led import hold
from led import take


class Txn:
    def __init__(self, num, store):
        self.num = num
        self.taken = take.Taken()
        self.taken.open(store)
        self.held = hold.Held()
        self.wrote = []
        self.marks = []
        self.bad = False

    def sets(self, k):
        if k not in self.wrote:
            self.wrote.append(k)

    def mark(self):
        self.marks.append((self.held.save(), list(self.wrote)))

    def cut(self):
        if self.marks:
            was, wrote = self.marks.pop()
            self.held.back(was)
            self.wrote = wrote
        else:
            self.held.back({})
            self.wrote = []
