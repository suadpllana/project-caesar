import heapq


class Walk:
    def __init__(self, store, marks, chunk):
        self.store = store
        self.marks = marks
        self.chunk = chunk
        self.cur = 0
        self.pile = []
        self.queued = set()
        self.read = 0

    def feed(self):
        depth = self.store.depth()
        while self.read < depth:
            self.read += 1
            kind, k = self.store.entry(self.read)[:2]
            if kind == "set" and k > self.cur and k not in self.queued:
                self.queued.add(k)
                heapq.heappush(self.pile, k)

    def take(self):
        self.feed()
        keys = []
        while self.pile and len(keys) < self.chunk:
            k = heapq.heappop(self.pile)
            self.queued.discard(k)
            if k <= self.cur or self.store.at(k) is None:
                continue
            keys.append(k)
        if not keys:
            self.marks.note(self.cur, self.cur, self.store.depth())
            return [], None
        mark = self.store.depth()
        self.marks.note(self.cur, keys[-1], mark)
        self.cur = keys[-1]
        return keys, mark
