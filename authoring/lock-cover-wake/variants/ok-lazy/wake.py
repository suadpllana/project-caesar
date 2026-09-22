import heapq


class Wake:
    """A heap of waiting heads, each entry stamped with the generation it was pushed at."""

    __slots__ = ("eng", "hp")

    def __init__(self, eng):
        self.eng = eng
        self.hp = []

    def touch(self, res):
        e = self.eng.ents.get(res)
        if e is None or not e.waiting():
            return
        heapq.heappush(self.hp, (e.head().seq, res, e.gen))

    def settle(self):
        eng = self.eng
        while self.hp:
            seq, res, gen = heapq.heappop(self.hp)
            e = eng.ents.get(res)
            if e is None or not e.waiting() or e.gen != gen:
                continue
            it = e.head()
            if e.hits_but(it.tid, it.m):
                continue
            eng.examine(e)
