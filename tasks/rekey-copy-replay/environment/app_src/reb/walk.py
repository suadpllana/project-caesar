class Walk:
    def __init__(self, store, marks, chunk):
        self.store = store
        self.marks = marks
        self.chunk = chunk
        self.cur = 0

    def take(self):
        top = self.cur + self.chunk
        keys = sorted(k for k in self.store.live() if self.cur < k <= top)
        if not keys:
            return [], None
        mark = self.store.depth()
        self.marks.note(self.cur, top, mark)
        self.cur = top
        return keys, mark
