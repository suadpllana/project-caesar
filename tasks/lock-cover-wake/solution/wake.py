import heapq


class Wake:
    __slots__ = ("eng", "hp", "dirty")

    def __init__(self, eng):
        self.eng = eng
        self.hp = []
        self.dirty = set()

    def touch(self, res):
        e = self.eng.ents.get(res)
        if e is None or not e.waiting():
            self.dirty.discard(res)
            return
        self.dirty.add(res)
        heapq.heappush(self.hp, (e.head().seq, res))

    def settle(self):
        eng = self.eng
        hp = self.hp
        while hp:
            seq, res = heapq.heappop(hp)
            if res not in self.dirty:
                continue
            e = eng.ents.get(res)
            if e is None or not e.waiting():
                self.dirty.discard(res)
                continue
            if e.head().seq != seq:
                continue
            self.dirty.discard(res)
            eng.examine(e)
