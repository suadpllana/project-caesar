BITS = 10


class Walk:
    def __init__(self, store, marks, chunk):
        self.store = store
        self.marks = marks
        self.chunk = chunk
        self.cur = 0
        self.bins = {}
        self.tops = []
        self.read = 0

    def feed(self):
        depth = self.store.depth()
        while self.read < depth:
            self.read += 1
            kind, k = self.store.entry(self.read)[:2]
            if kind != "set" or k <= self.cur:
                continue
            slot = k >> BITS
            room = self.bins.get(slot)
            if room is None:
                room = self.bins[slot] = set()
                self.tops.append(slot)
                self.tops.sort()
            room.add(k)

    def take(self):
        self.feed()
        keys = []
        while self.tops and len(keys) < self.chunk:
            slot = self.tops[0]
            room = self.bins[slot]
            ready = sorted(room)
            for k in ready:
                if len(keys) >= self.chunk:
                    break
                room.discard(k)
                if k <= self.cur or self.store.at(k) is None:
                    continue
                keys.append(k)
            if not room:
                del self.bins[slot]
                self.tops.pop(0)
        if not keys:
            return [], None
        mark = self.store.depth()
        self.marks.note(self.cur, keys[-1], mark)
        self.cur = keys[-1]
        return keys, mark
