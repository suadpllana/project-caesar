class Walk:
    def __init__(self, store, marks, chunk):
        self.store = store
        self.marks = marks
        self.chunk = chunk
        self.cur = 0

    def take(self):
        keys = sorted(k for k in self.store.live() if k > self.cur)[:self.chunk]
        if not keys:
            return [], None
        mark = self.store.depth()
        self.marks.note(self.cur, keys[-1], mark)
        self.cur = keys[-1]
        return keys, mark
