class Sift:
    def __init__(self, store, walk, marks):
        self.store = store
        self.walk = walk
        self.marks = marks
        self.next = 1

    def take(self, n):
        out = []
        if n <= 0:
            return out
        top = min(self.store.depth(), self.next + n - 1)
        cur = self.walk.cur
        while self.next <= top:
            pos = self.next
            self.next += 1
            kind, k, a, b, c = self.store.entry(pos)
            if k > cur:
                verdict = "ahead"
            elif pos <= self.marks.at(k):
                verdict = "seen"
            else:
                verdict = "done"
            out.append((pos, kind, k, a, b, c, verdict))
        return out
